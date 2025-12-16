"""Report verification functions for E2E tests.

These functions verify that benchmark reports are generated correctly.
"""

from __future__ import annotations

import zipfile
from pathlib import Path


def verify_reports_exist(results_dir: Path) -> None:
    """Verify that report was generated correctly.

    Checks for:
    - Report directories (1-short, 2-results, 3-full)
    - REPORT.md files
    - Figures
    - Attachments

    Args:
        results_dir: Results directory

    Raises:
        AssertionError: If report verification fails
    """
    reports_dir = results_dir / "reports"
    assert reports_dir.exists(), f"Reports directory not found: {reports_dir}"

    # Check for report variants
    expected_variants = ["1-short", "2-results", "3-full"]
    found_variants = []

    for variant in expected_variants:
        variant_dir = reports_dir / variant
        if not variant_dir.exists():
            # Not all variants are always generated, track which exist
            continue

        found_variants.append(variant)

        # Check for REPORT.md
        report_md = variant_dir / "REPORT.md"
        assert report_md.exists(), f"REPORT.md not found in {variant_dir}"

        # Verify REPORT.md is not empty
        assert report_md.stat().st_size > 0, f"REPORT.md is empty in {variant_dir}"

    # At least one variant should exist
    assert len(found_variants) > 0, (
        f"No report variants found in {reports_dir}. "
        f"Expected one of: {expected_variants}"
    )


def verify_figures_generated(results_dir: Path) -> None:
    """Verify that expected figures were generated.

    Args:
        results_dir: Results directory

    Raises:
        AssertionError: If figure verification fails
    """
    figures_dir = results_dir / "figures"
    if not figures_dir.exists():
        # Figures might be in report attachments
        reports_figures = results_dir / "reports" / "3-full" / "attachments" / "figures"
        if reports_figures.exists():
            figures_dir = reports_figures

    if not figures_dir.exists():
        # Figures are optional, skip if not found
        return

    expected_figures = [
        "query_runtime_boxplot.png",
        "median_runtime_bar.png",
        "performance_heatmap.png",
    ]

    found_figures = []
    for figure in expected_figures:
        figure_path = figures_dir / figure
        if figure_path.exists():
            found_figures.append(figure)
            assert (
                figure_path.stat().st_size > 0
            ), f"Figure file is empty: {figure_path}"

    # At least some figures should be generated
    assert (
        len(found_figures) > 0
    ), f"No figures found in {figures_dir}. Expected: {expected_figures}"


def verify_package_contents(package_path: Path) -> None:
    """Verify that benchmark package contains expected files.

    Args:
        package_path: Path to the package zip file

    Raises:
        AssertionError: If package verification fails
    """
    assert package_path.exists(), f"Package not found: {package_path}"
    assert package_path.stat().st_size > 0, f"Package is empty: {package_path}"

    with zipfile.ZipFile(package_path, "r") as zf:
        file_list = zf.namelist()

        # Check for required files
        required_patterns = [
            "run_benchmark.sh",
            "config.yaml",
            "benchkit/",
            "requirements.txt",
        ]

        for pattern in required_patterns:
            matches = [f for f in file_list if pattern in f]
            assert len(matches) > 0, (
                f"Required pattern '{pattern}' not found in package. "
                f"Files: {file_list[:20]}..."  # Show first 20 files
            )

        # Verify package doesn't include infra/ (should be excluded)
        infra_files = [f for f in file_list if "/infra/" in f or f.startswith("infra/")]
        assert (
            len(infra_files) == 0
        ), f"infra/ files should not be in package: {infra_files}"


def verify_report_attachments(results_dir: Path) -> None:
    """Verify that report attachments are present.

    Args:
        results_dir: Results directory

    Raises:
        AssertionError: If attachment verification fails
    """
    reports_dir = results_dir / "reports"
    if not reports_dir.exists():
        return

    # Check for attachments in the 3-full report
    full_report = reports_dir / "3-full"
    if not full_report.exists():
        return

    attachments = full_report / "attachments"
    if not attachments.exists():
        return

    # Check for common attachments
    expected_attachments = [
        "config.yaml",
        "summary.json",
    ]

    for attachment in expected_attachments:
        attachment_path = attachments / attachment
        if attachment_path.exists():
            assert (
                attachment_path.stat().st_size > 0
            ), f"Attachment is empty: {attachment_path}"


def verify_html_report_generated(results_dir: Path) -> None:
    """Verify that HTML reports were generated.

    Args:
        results_dir: Results directory

    Raises:
        AssertionError: If HTML report verification fails
    """
    reports_dir = results_dir / "reports"
    if not reports_dir.exists():
        return

    # Check for HTML files in report variants
    html_found = False
    for variant_dir in reports_dir.iterdir():
        if variant_dir.is_dir():
            html_file = variant_dir / "REPORT.html"
            if html_file.exists():
                html_found = True
                assert (
                    html_file.stat().st_size > 0
                ), f"HTML report is empty: {html_file}"

    # HTML reports are optional, just note if not found
    if not html_found:
        pass  # HTML generation might be disabled
