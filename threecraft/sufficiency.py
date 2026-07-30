"""Route-aware sufficiency policy for the deterministic local MVP."""

from __future__ import annotations

from .contracts import Issue, SensePack, SufficiencyReport


def assess_sufficiency(sense: SensePack, *, route: str = "relief") -> SufficiencyReport:
    issues: list[Issue] = []

    if min(sense.width, sense.height) < 128:
        issues.append(
            Issue(
                "RESOLUTION_TOO_LOW",
                "blocker",
                "The image's shorter side is less than 128 px.",
                ("upload-higher-resolution",),
                {"width": sense.width, "height": sense.height},
            )
        )
    elif min(sense.width, sense.height) < 256:
        issues.append(
            Issue(
                "RESOLUTION_MARGINAL",
                "warning",
                "A larger image will preserve the silhouette more reliably.",
                ("upload-higher-resolution", "use-16-block-resolution"),
            )
        )

    if sense.foreground_bounds is None or sense.foreground_ratio <= 0.001:
        issues.append(
            Issue(
                "FOREGROUND_EMPTY",
                "blocker",
                "No foreground subject was found for conversion.",
                ("upload-another-image", "use-transparent-background"),
            )
        )
    elif sense.foreground_ratio < 0.01:
        issues.append(
            Issue(
                "SUBJECT_TOO_SMALL",
                "blocker",
                "The subject is too small in the image.",
                ("crop-around-subject", "upload-another-image"),
                {"foregroundRatio": sense.foreground_ratio},
            )
        )

    if sense.foreground_ratio > 0.97:
        issues.append(
            Issue(
                "BACKGROUND_NOT_SEPARATED",
                "warning",
                "The background and subject may not be separated clearly enough.",
                ("use-transparent-background", "upload-simpler-background"),
            )
        )
    if sense.touches_frame:
        issues.append(
            Issue(
                "SUBJECT_TOUCHES_FRAME",
                "warning",
                "The subject touches the image boundary and may be cropped.",
                ("add-padding", "upload-full-object"),
            )
        )
    if sense.component_count > 4:
        issues.append(
            Issue(
                "MULTIPLE_SUBJECTS",
                "warning",
                "Multiple disconnected foreground regions may make a single-subject result unstable.",
                ("use-single-object-image",),
                {"componentCount": sense.component_count},
            )
        )
    if route == "relief":
        issues.append(
            Issue(
                "RELIEF_2_5D",
                "info",
                "The current local MVP creates a front-view 2.5D relief.",
                ("configure-single-image-mesh-provider",),
            )
        )

    blocker_count = sum(issue.severity == "blocker" for issue in issues)
    warning_count = sum(issue.severity == "warning" for issue in issues)
    score = max(0.0, 1.0 - blocker_count * 0.6 - warning_count * 0.08)
    if blocker_count:
        return SufficiencyReport("reject", False, "abort", score, route, tuple(issues))
    if warning_count:
        return SufficiencyReport("conditional", True, "continue", score, route, tuple(issues))
    return SufficiencyReport("pass", True, "continue", score, route, tuple(issues))
