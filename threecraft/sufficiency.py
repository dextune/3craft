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
                "이미지의 짧은 변이 128px보다 작습니다.",
                ("upload-higher-resolution",),
                {"width": sense.width, "height": sense.height},
            )
        )
    elif min(sense.width, sense.height) < 256:
        issues.append(
            Issue(
                "RESOLUTION_MARGINAL",
                "warning",
                "더 큰 이미지를 사용하면 윤곽이 안정적으로 보존됩니다.",
                ("upload-higher-resolution", "use-16-block-resolution"),
            )
        )

    if sense.foreground_bounds is None or sense.foreground_ratio <= 0.001:
        issues.append(
            Issue(
                "FOREGROUND_EMPTY",
                "blocker",
                "변환할 전경 물체를 찾지 못했습니다.",
                ("upload-another-image", "use-transparent-background"),
            )
        )
    elif sense.foreground_ratio < 0.01:
        issues.append(
            Issue(
                "SUBJECT_TOO_SMALL",
                "blocker",
                "물체가 이미지에서 너무 작습니다.",
                ("crop-around-subject", "upload-another-image"),
                {"foregroundRatio": sense.foreground_ratio},
            )
        )

    if sense.foreground_ratio > 0.97:
        issues.append(
            Issue(
                "BACKGROUND_NOT_SEPARATED",
                "warning",
                "배경과 물체가 충분히 분리되지 않았을 수 있습니다.",
                ("use-transparent-background", "upload-simpler-background"),
            )
        )
    if sense.touches_frame:
        issues.append(
            Issue(
                "SUBJECT_TOUCHES_FRAME",
                "warning",
                "물체가 이미지 경계에 닿아 일부가 잘렸을 수 있습니다.",
                ("add-padding", "upload-full-object"),
            )
        )
    if sense.component_count > 4:
        issues.append(
            Issue(
                "MULTIPLE_SUBJECTS",
                "warning",
                "분리된 전경 영역이 많아 단일 물체 결과가 불안정할 수 있습니다.",
                ("use-single-object-image",),
                {"componentCount": sense.component_count},
            )
        )
    if route == "relief":
        issues.append(
            Issue(
                "RELIEF_2_5D",
                "info",
                "현재 로컬 MVP는 정면 기반 2.5D relief를 생성합니다.",
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
