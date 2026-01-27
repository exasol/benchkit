"""Exasol cluster management using c4 and confd_client.

This module handles cluster management operations like getting play IDs,
executing confd_client commands, installing licenses, and configuring
database parameters.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from benchkit.common import exclude_from_package

if TYPE_CHECKING:
    from .system import ExasolSystem


class ExasolClusterManager:
    """Handles Exasol cluster management operations.

    This class encapsulates operations that interact with the Exasol cluster
    via the c4 tool and confd_client commands.
    """

    def __init__(self, system: ExasolSystem):
        """Initialize the cluster manager.

        Args:
            system: Parent ExasolSystem instance for shared state access
        """
        self._system = system

    def _log(self, message: str) -> None:
        """Log a message using the parent system's logger."""
        self._system._log(message)

    def get_cluster_play_id(self) -> str | None:
        """Get the cluster play_id from c4 ps command.

        Returns:
            The play_id string, or None if not found
        """
        system = self._system

        system.record_setup_command(
            "c4 ps",
            "Get cluster play ID for confd_client operations",
            "cluster_management",
        )

        ps_result = system.execute_command("c4 ps", timeout=30)
        if ps_result["success"]:
            lines = ps_result.get("stdout", "").strip().split("\n")
            if len(lines) >= 2:
                play_id: str = lines[1].split()[1]
                system.record_setup_note(f"Found cluster play ID: {play_id}")
                return play_id
            else:
                system.record_setup_note(
                    "⚠ Warning: Could not parse play ID from c4 ps output"
                )
                return None
        else:
            system.record_setup_note(
                f"⚠ Warning: Failed to get cluster info: {ps_result.get('stderr', 'Unknown error')}"
            )
            return None

    @exclude_from_package
    def execute_confd_client_command(
        self,
        play_id: str,
        confd_command: str,
        description: str,
        category: str = "configuration",
        silent: bool = False,
    ) -> bool:
        """Execute a confd_client command through c4 connect.

        Args:
            play_id: The cluster play ID
            confd_command: The confd_client command to execute
            description: Description for logging
            category: Category for command recording
            silent: If True, don't record the command

        Returns:
            True if command succeeded
        """
        system = self._system
        full_cmd = f"c4 connect -s cos -i {play_id} -- {confd_command}"

        if not silent:
            system.record_setup_command(confd_command, description, category)

        result = system.execute_command(full_cmd, timeout=300)
        return bool(result.get("success", False))

    @exclude_from_package
    def install_license_file(self, play_id: str, license_file_path: str) -> None:
        """Install Exasol license file using c4 connect.

        Args:
            play_id: The cluster play ID
            license_file_path: Path to the license file
        """
        system = self._system
        system.record_setup_note("Installing Exasol license...")

        json_txt = '"{< -}"'
        license_cmd = f"""cat {license_file_path} | c4 connect -s cos -i {play_id} -- confd_client license_upload license: '\\"{json_txt}\\"'"""

        system.record_setup_command(
            "confd_client license_upload license: <LICENSE_CONTENT>",
            "Install Exasol license file",
            "license_setup",
        )

        license_result = system.execute_command(license_cmd, timeout=120)
        if license_result["success"]:
            system.record_setup_note("Exasol license installed successfully")
        else:
            system.record_setup_note(
                f"Warning: License installation failed: {license_result.get('stderr', 'Unknown error')}"
            )

    @exclude_from_package
    def configure_database_parameters(self, play_id: str, db_params: list[str]) -> bool:
        """Configure Exasol database parameters using c4 connect.

        This method:
        1. Stops the database
        2. Applies parameter configuration
        3. Restarts the database
        4. Waits for database to be fully initialized

        Args:
            play_id: The cluster play ID
            db_params: List of database parameters to configure

        Returns:
            True if configuration succeeded and database is running
        """
        system = self._system
        system.record_setup_note("Configuring Exasol database parameters...")
        self._log(f"Configuring {len(db_params)} database parameters: {db_params}")

        # Step 1: Stop the database
        system.record_setup_note("Stopping database for parameter configuration...")
        stop_command = "confd_client db_stop db_name: Exasol"

        system.record_setup_command(
            stop_command,
            "Stop Exasol database for parameter configuration",
            "database_tuning",
        )

        self._log("Stopping database for parameter configuration...")
        if not self.execute_confd_client_command(
            play_id,
            stop_command,
            "Stop Exasol database for parameter configuration",
            "database_tuning",
        ):
            system.record_setup_note(
                "⚠ Warning: Failed to stop database for parameter configuration"
            )
            self._log("✗ Failed to stop database")
            return False
        else:
            self._log("✓ Database stopped successfully")

        # Step 2: Configure database parameters
        params_with_quotes = ["'" + param + "'" for param in db_params]
        params_str = ",".join(params_with_quotes)
        params_command = (
            f'confd_client db_configure db_name: Exasol params_add: "[{params_str}]"'
        )

        system.record_setup_command(
            params_command,
            "Configure Exasol database parameters for analytical workload optimization",
            "database_tuning",
        )

        self._log(f"Configuring database with parameters: {params_str}")
        if not self.execute_confd_client_command(
            play_id,
            params_command,
            "Configure Exasol database parameters for analytical workload optimization",
            "database_tuning",
        ):
            system.record_setup_note("Warning: Database parameter configuration failed")
            self._log("✗ Failed to configure database parameters")
            return False
        else:
            self._log("✓ Database parameters configured successfully")

        # Step 3: Start the database
        system.record_setup_note("Starting database with new parameters...")
        start_command = "confd_client db_start db_name: Exasol"

        self._log("Starting database with new parameters...")
        if not self.execute_confd_client_command(
            play_id,
            start_command,
            "Starting database with new parameters",
            "database_tuning",
        ):
            system.record_setup_note(
                "⚠ Warning: Failed to start database after parameter configuration"
            )
            self._log("✗ Failed to start database after parameter configuration")
            return False
        else:
            self._log("✓ Database start command completed")

        # Step 4: Wait for database to be fully initialized
        system.record_setup_note("Waiting for database to be fully initialized...")
        self._log("Waiting for database to be fully initialized...")
        if self.wait_for_database_ready(play_id):
            system.record_setup_note(
                "✓ Database parameters configured and database started successfully"
            )
            self._log("✓ Database is fully ready after parameter configuration")
            return True
        else:
            system.record_setup_note(
                "⚠ Warning: Database started but initialization check failed"
            )
            self._log(
                "✗ Database initialization check failed after parameter configuration"
            )
            return False

    @exclude_from_package
    def wait_for_database_ready(
        self, play_id: str, max_attempts: int = 60, delay: int = 5
    ) -> bool:
        """Wait for database to be fully initialized and connectable.

        Args:
            play_id: The cluster play ID
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds

        Returns:
            True if database became ready within timeout
        """
        system = self._system

        for attempt in range(max_attempts):
            # Check if stage6 is complete
            check_cmd = f'c4 connect -s cos -i {play_id} -- tail /exa/logs/cored/exainit.log | grep "stage6: All stages finished."'

            result = system.execute_command(check_cmd, timeout=30, record=False)
            stage6_complete = result.get(
                "success", False
            ) and "stage6: All stages finished." in result.get("stdout", "")

            # Check if database is connectable
            db_connectable = system.is_healthy(quiet=True)

            if stage6_complete and db_connectable:
                return True

            if attempt < max_attempts - 1:
                time.sleep(delay)

        return False

    @exclude_from_package
    def cleanup_disturbing_services(self, play_id: str) -> bool:
        """Remove rapid, eventd, healthd services that interfere with benchmarks.

        Args:
            play_id: The cluster play ID

        Returns:
            True if cleanup succeeded or no services needed removal
        """
        system = self._system

        try:
            cosps_result = system.execute_command(
                f"c4 connect -s cos -i {play_id} -- cosps", timeout=30, record=False
            )
            if not cosps_result.get("success", False):
                return False

            service_ids = {}
            for line in cosps_result.get("stdout", "").split("\n"):
                parts = line.split()
                if len(parts) >= 7 and not line.strip().startswith(
                    ("ROOT", "--", "ID")
                ):
                    for target in ["rapid", "eventd", "healthd"]:
                        if target in parts[6]:
                            service_ids[target] = parts[0]
                            break

            if not service_ids:
                return True

            removed = sum(
                1
                for sid in service_ids.values()
                if system.execute_command(
                    f"c4 connect -s cos -i {play_id} -- cosrm -a {sid}",
                    timeout=30,
                    record=False,
                ).get("success", False)
            )
            return removed > 0

        except Exception:
            return False
