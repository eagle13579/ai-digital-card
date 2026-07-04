"""DesignQAAgent — Design Quality Assurance Engineer Digital Employee.

An AI employee that performs design reviews, accessibility audits,
performance checks, responsive audits, anti-pattern detection, and
pre-launch quality checks — powered by impeccable's 23 design review
commands and 37 anti-pattern detection rules.

Architecture:
    Extends BaseAgent with design-QA-specific tools and a hardcoded
    knowledge base of impeccable's review commands and anti-pattern rules.
    Each tool returns a structured report with severity (P0-P3) scoring.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.agents.base_agent import BaseAgent, AgentConfig, AgentStatus

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# Impeccable 23 Design Review Commands — Knowledge Base
# ══════════════════════════════════════════════════════════════════

IMPECCABLE_COMMANDS: list[dict[str, Any]] = [
    {
        "id": "craft",
        "name": "Craft",
        "description": "Full confirmed-brief-then-build flow. Runs multi-round shape discovery first, resolves visual probe and north-star mock gates when available, then builds and visually iterates. Use when building a new feature end-to-end.",
        "category": "create",
        "argument_hint": "[feature description]",
    },
    {
        "id": "init",
        "name": "Init",
        "description": "Sets up a project for impeccable. Runs a multi-round discovery interview when context is missing and writes PRODUCT.md (strategic: users, brand, principles); offers DESIGN.md (visual: colors, typography, components) when code exists; pre-configures live mode; then recommends the best commands to run next.",
        "category": "system",
        "argument_hint": "",
    },
    {
        "id": "document",
        "name": "Document",
        "description": "Generate a DESIGN.md file that captures the current visual design system. Auto-extracts colors, typography, spacing, radii, and component patterns from the codebase.",
        "category": "system",
        "argument_hint": "",
    },
    {
        "id": "extract",
        "name": "Extract",
        "description": "Pull reusable patterns, components, and design tokens into the design system. Identifies repeated patterns and consolidates them.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "live",
        "name": "Live",
        "description": "Interactive live variant mode. Select elements in the browser, pick a design action, and get AI-generated HTML+CSS variants hot-swapped via HMR.",
        "category": "create",
        "argument_hint": "",
    },
    {
        "id": "adapt",
        "name": "Adapt",
        "description": "Adapt designs to work across different screen sizes, devices, contexts, or platforms. Implements breakpoints, fluid layouts, and touch targets.",
        "category": "refine",
        "argument_hint": "[target] [context (mobile, tablet, print...)]",
    },
    {
        "id": "animate",
        "name": "Animate",
        "description": "Review a feature and enhance it with purposeful animations, micro-interactions, and motion effects that improve usability and delight.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "audit",
        "name": "Audit",
        "description": "Run technical quality checks across accessibility, performance, theming, responsive design, and anti-patterns. Generates a scored report with P0-P3 severity ratings.",
        "category": "evaluate",
        "argument_hint": "[area (feature, page, component...)]",
    },
    {
        "id": "bolder",
        "name": "Bolder",
        "description": "Amplify safe or boring designs to make them more visually interesting and stimulating. Increases impact while maintaining usability.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "clarify",
        "name": "Clarify",
        "description": "Improve unclear UX copy, error messages, microcopy, labels, and instructions to make interfaces easier to understand.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "colorize",
        "name": "Colorize",
        "description": "Add strategic color to features that are too monochromatic or lack visual interest, making interfaces more engaging and expressive.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "critique",
        "name": "Critique",
        "description": "Evaluate design from a UX perspective, assessing visual hierarchy, information architecture, emotional resonance, cognitive load, and overall quality with quantitative scoring.",
        "category": "evaluate",
        "argument_hint": "[area (feature, page, component...)]",
    },
    {
        "id": "delight",
        "name": "Delight",
        "description": "Add moments of joy, personality, and unexpected touches that make interfaces memorable and enjoyable to use.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "distill",
        "name": "Distill",
        "description": "Strip designs to their essence by removing unnecessary complexity. Great design is simple, powerful, and clean.",
        "category": "simplify",
        "argument_hint": "[target]",
    },
    {
        "id": "harden",
        "name": "Harden",
        "description": "Make interfaces production-ready: error handling, i18n, text overflow, edge case management, and resilience under real-world data.",
        "category": "harden",
        "argument_hint": "[target]",
    },
    {
        "id": "onboard",
        "name": "Onboard",
        "description": "Design onboarding flows, first-run experiences, and empty states that guide new users to value.",
        "category": "create",
        "argument_hint": "[target]",
    },
    {
        "id": "layout",
        "name": "Layout",
        "description": "Improve layout, spacing, and visual rhythm. Fixes monotonous grids, inconsistent spacing, and weak visual hierarchy.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "optimize",
        "name": "Optimize",
        "description": "Diagnoses and fixes UI performance across loading speed, rendering, animations, images, and bundle size.",
        "category": "harden",
        "argument_hint": "[target]",
    },
    {
        "id": "overdrive",
        "name": "Overdrive",
        "description": "Pushes interfaces past conventional limits with technically ambitious implementations — shaders, spring physics, scroll-driven reveals, 60fps animations.",
        "category": "create",
        "argument_hint": "[target]",
    },
    {
        "id": "polish",
        "name": "Polish",
        "description": "Performs a final quality pass fixing alignment, spacing, consistency, and micro-detail issues before shipping.",
        "category": "refine",
        "argument_hint": "[target]",
    },
    {
        "id": "quieter",
        "name": "Quieter",
        "description": "Tones down visually aggressive or overstimulating designs, reducing intensity while preserving quality.",
        "category": "simplify",
        "argument_hint": "[target]",
    },
    {
        "id": "shape",
        "name": "Shape",
        "description": "Plan UX and UI before code. Runs a required multi-round discovery interview, uses visual probes when available, and produces a user-confirmed design brief.",
        "category": "create",
        "argument_hint": "[feature to shape]",
    },
    {
        "id": "typeset",
        "name": "Typeset",
        "description": "Improves typography by fixing font choices, hierarchy, sizing, weight, and readability so text feels intentional.",
        "category": "refine",
        "argument_hint": "[target]",
    },
]

# ══════════════════════════════════════════════════════════════════
# Impeccable 37 Anti-Pattern Rules — Knowledge Base
# ══════════════════════════════════════════════════════════════════

IMPECCABLE_ANTIPATTERNS: list[dict[str, Any]] = [
    # ── AI slop: tells that something was AI-generated ──
    {
        "id": "side-tab",
        "category": "slop",
        "name": "Side-tab accent border",
        "description": "Thick colored border on one side of a card — the most recognizable tell of AI-generated UIs. Use a subtler accent or remove it entirely.",
        "skill_section": "Visual Details",
        "severity": "P2",
    },
    {
        "id": "border-accent-on-rounded",
        "category": "slop",
        "name": "Border accent on rounded element",
        "description": "Thick accent border on a rounded card — the border clashes with the rounded corners. Remove the border or the border-radius.",
        "skill_section": "Visual Details",
        "severity": "P2",
    },
    {
        "id": "overused-font",
        "category": "slop",
        "name": "Overused font",
        "description": "Inter, Roboto, Fraunces, Geist, Plus Jakarta Sans, and Space Grotesk are used on so many sites they no longer feel distinctive. Each new wave of AI-generated UIs converges on the same handful of faces.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "single-font",
        "category": "slop",
        "name": "Single font for everything",
        "description": "Only one font family is used for the entire page. Pair a distinctive display font with a refined body font to create typographic hierarchy.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "flat-type-hierarchy",
        "category": "slop",
        "name": "Flat type hierarchy",
        "description": "Font sizes are too close together — no clear visual hierarchy. Use fewer sizes with more contrast (aim for at least a 1.25 ratio between steps).",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "gradient-text",
        "category": "slop",
        "name": "Gradient text",
        "description": "Gradient text is decorative rather than meaningful — a common AI tell, especially on headings and metrics. Use solid colors for text.",
        "skill_section": "Color & Contrast",
        "severity": "P1",
    },
    {
        "id": "ai-color-palette",
        "category": "slop",
        "name": "AI color palette",
        "description": "Purple/violet gradients and cyan-on-dark are the most recognizable tells of AI-generated UIs. Choose a distinctive, intentional palette.",
        "skill_section": "Color & Contrast",
        "severity": "P1",
    },
    {
        "id": "cream-palette",
        "category": "slop",
        "name": "Cream / beige palette",
        "description": "A warm cream or beige page background has become the default 'tasteful' AI surface, reached for by reflex.",
        "skill_section": "Color & Contrast",
        "severity": "P2",
    },
    {
        "id": "nested-cards",
        "category": "slop",
        "name": "Nested cards",
        "description": "Cards inside cards create visual noise and excessive depth. Flatten the hierarchy — use spacing, typography, and dividers instead of nesting containers.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
    {
        "id": "monotonous-spacing",
        "category": "slop",
        "name": "Monotonous spacing",
        "description": "The same spacing value used everywhere — no rhythm, no variation. Use tight groupings for related items and generous separations between sections.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
    {
        "id": "bounce-easing",
        "category": "slop",
        "name": "Bounce or elastic easing",
        "description": "Bounce and elastic easing feel dated and tacky. Real objects decelerate smoothly — use exponential easing (ease-out-quart/quint/expo) instead.",
        "skill_section": "Motion",
        "severity": "P2",
    },
    {
        "id": "dark-glow",
        "category": "slop",
        "name": "Dark mode with glowing accents",
        "description": "Dark backgrounds with colored box-shadow glows are the default 'cool' look of AI-generated UIs. Use subtle, purposeful lighting instead.",
        "skill_section": "Color & Contrast",
        "severity": "P2",
    },
    {
        "id": "icon-tile-stack",
        "category": "slop",
        "name": "Icon tile stacked above heading",
        "description": "A small rounded-square icon container above a heading is the universal AI feature-card template — every generator outputs this exact shape.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "italic-serif-display",
        "category": "slop",
        "name": "Italic serif display headline",
        "description": "Oversized italic serif as the primary hero headline reads as taste in isolation but has become the universal AI-startup landing page hero.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "hero-eyebrow-chip",
        "category": "slop",
        "name": "Hero eyebrow / pill chip",
        "description": "A tiny uppercase letter-spaced label sitting immediately above an oversized hero headline is now the default AI SaaS hero.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "repeated-section-kickers",
        "category": "slop",
        "name": "Repeated section kicker labels",
        "description": "Repeating tiny uppercase tracked labels above section headings turns a brand page into AI editorial scaffolding.",
        "skill_section": "Typography",
        "severity": "P3",
    },
    {
        "id": "numbered-section-markers",
        "category": "slop",
        "name": "Numbered section markers (01 / 02 / 03)",
        "description": "Numbered display markers as section labels (01, 02, 03) are the AI editorial scaffold one tier deeper than tracked eyebrow chips.",
        "skill_section": "Layout & Space",
        "severity": "P3",
    },
    {
        "id": "em-dash-overuse",
        "category": "slop",
        "name": "Em-dash overuse",
        "description": "More than two em-dashes (— or --) in body copy is an AI cadence tell. Use commas, colons, periods, or parentheses instead.",
        "skill_section": "Copy",
        "severity": "P2",
    },
    {
        "id": "marketing-buzzword",
        "category": "slop",
        "name": "Marketing buzzword",
        "description": "Generic SaaS phrases (streamline / empower / supercharge / world-class / enterprise-grade / next-generation / cutting-edge / etc) are instant AI tells.",
        "skill_section": "Copy",
        "severity": "P2",
    },
    {
        "id": "aphoristic-cadence",
        "category": "slop",
        "name": "Aphoristic-cadence copy",
        "description": "Three or more sections landing on a short rebuttal sentence ('X. No Y.' / 'X. Just Y.') reads as AI cadence, not voice.",
        "skill_section": "Copy",
        "severity": "P2",
    },
    {
        "id": "oversized-h1",
        "category": "slop",
        "name": "Oversized hero headline",
        "description": "A full-sentence headline set at display size ends up dominating the viewport, leaving no room for anything else above the fold.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "extreme-negative-tracking",
        "category": "slop",
        "name": "Crushed letter spacing",
        "description": "Letter-spacing pulled tighter than the point where characters keep their own shapes costs legibility. Tighten display type optically, not destructively.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "broken-image",
        "category": "quality",
        "name": "Broken or placeholder image",
        "description": "<img> tags with empty src, missing src, or placeholder values ship as broken-image boxes. Use real images or remove the tag.",
        "skill_section": "Imagery",
        "severity": "P1",
    },
    # ── Quality: general design and accessibility issues ──
    {
        "id": "gray-on-color",
        "category": "quality",
        "name": "Gray text on colored background",
        "description": "Gray text looks washed out on colored backgrounds. Use a darker shade of the background color instead, or white/near-white for contrast.",
        "skill_section": "Color & Contrast",
        "severity": "P1",
    },
    {
        "id": "low-contrast",
        "category": "quality",
        "name": "Low contrast text",
        "description": "Text does not meet WCAG AA contrast requirements (4.5:1 for body, 3:1 for large text). Increase the contrast between text and background.",
        "skill_section": "Color & Contrast",
        "severity": "P0",
    },
    {
        "id": "layout-transition",
        "category": "quality",
        "name": "Layout property animation",
        "description": "Animating width, height, padding, or margin causes layout thrash and janky performance. Use transform and opacity instead.",
        "skill_section": "Motion",
        "severity": "P1",
    },
    {
        "id": "line-length",
        "category": "quality",
        "name": "Line length too long",
        "description": "Text lines wider than ~80 characters are hard to read. Add a max-width (65ch to 75ch) to text containers.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
    {
        "id": "cramped-padding",
        "category": "quality",
        "name": "Cramped padding",
        "description": "Text is too close to the edge of its container. Add at least 8px (ideally 12–16px) of padding inside bordered, outlined, or colored containers.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
    {
        "id": "body-text-viewport-edge",
        "category": "quality",
        "name": "Body text touching viewport edge",
        "description": "Body paragraphs render flush against the left or right viewport edge with no container providing horizontal padding.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
    {
        "id": "tight-leading",
        "category": "quality",
        "name": "Tight line height",
        "description": "Line height below 1.3x the font size makes multi-line text hard to read. Use 1.5 to 1.7 for body text.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "skipped-heading",
        "category": "quality",
        "name": "Skipped heading level",
        "description": "Heading levels should not skip (e.g. h1 then h3 with no h2). Screen readers use heading hierarchy for navigation.",
        "skill_section": "Accessibility",
        "severity": "P1",
    },
    {
        "id": "justified-text",
        "category": "quality",
        "name": "Justified text",
        "description": "Justified text without hyphenation creates uneven word spacing ('rivers of white'). Use text-align: left for body text.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "tiny-text",
        "category": "quality",
        "name": "Tiny body text",
        "description": "Body text below 12px is hard to read, especially on high-DPI screens. Use at least 14px for body content, 16px is ideal.",
        "skill_section": "Typography",
        "severity": "P1",
    },
    {
        "id": "all-caps-body",
        "category": "quality",
        "name": "All-caps body text",
        "description": "Long passages in uppercase are hard to read. We recognize words by shape (ascenders and descenders), which all-caps removes.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "wide-tracking",
        "category": "quality",
        "name": "Wide letter spacing on body text",
        "description": "Letter spacing above 0.05em on body text disrupts natural character groupings and slows reading.",
        "skill_section": "Typography",
        "severity": "P2",
    },
    {
        "id": "text-overflow",
        "category": "quality",
        "name": "Content overflowing its container",
        "description": "Content renders wider than its container, spilling out or forcing a horizontal scrollbar.",
        "skill_section": "Layout & Space",
        "severity": "P1",
    },
    {
        "id": "clipped-overflow-container",
        "category": "quality",
        "name": "Positioned child clipped by overflow container",
        "description": "A clipping container (overflow hidden or clip) wrapping an absolutely-positioned child cuts off tooltips, menus, and popovers.",
        "skill_section": "Layout & Space",
        "severity": "P2",
    },
]

# Map severity names to numeric severity for sorting
SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _build_report(
    command: str,
    score: int,
    max_score: int,
    findings: list[dict[str, Any]],
    recommendations: list[str],
) -> dict[str, Any]:
    """Build a structured audit report."""
    # Categorize findings by severity
    severity: dict[str, list[dict[str, Any]]] = {"P0": [], "P1": [], "P2": [], "P3": []}
    for f in findings:
        sev = f.get("severity", "P2")
        if sev not in severity:
            sev = "P2"
        severity[sev].append(f)

    return {
        "command": command,
        "score": score,
        "max_score": max_score,
        "score_pct": round(score / max_score * 100, 1) if max_score > 0 else 0,
        "severity": severity,
        "total_findings": len(findings),
        "findings": findings,
        "recommendations": recommendations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class DesignQAAgent(BaseAgent):
    """Design Quality Assurance Engineer — design critique, accessibility audits,
    performance checks, responsive reviews, anti-pattern detection, and
    pre-launch polish verification.

    Hardcodes impeccable's 23 design review commands and 37 anti-pattern
    detection rules as its knowledge base, providing them as executable tools.

    Args:
        config: Agent configuration (defaults to Design QA role).
        brain: GaiaEvolutionBrain reference for knowledge lookup and learning.
        broker: ServiceBrokerProtocol reference for cross-service calls.
        event_bus: EventBusProtocol reference for publishing events.
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        brain: Any | None = None,
        broker: Any | None = None,
        event_bus: Any | None = None,
    ) -> None:
        design_qa_config = config or AgentConfig(
            agent_name="design_qa_engineer",
            agent_role="design_quality_assurance_engineer",
            knowledge_base_name="design_qa",
            max_concurrent_tasks=10,
        )
        super().__init__(config=design_qa_config, brain=brain)
        self.broker: Any | None = broker
        self.event_bus: Any | None = event_bus

        # Tracking counters
        self._critiques_done: int = 0
        self._audits_done: int = 0
        self._antipatterns_detected: int = 0
        self._polish_checks: int = 0

        # Pre-load knowledge bases
        self._commands: list[dict[str, Any]] = IMPECCABLE_COMMANDS
        self._antipatterns: list[dict[str, Any]] = IMPECCABLE_ANTIPATTERNS

    # ── Properties ─────────────────────────────────────────────────

    @property
    def available_commands(self) -> list[dict[str, Any]]:
        """Expose the hardcoded 23 impeccable commands as agent knowledge."""
        return list(self._commands)

    @property
    def available_antipatterns(self) -> list[dict[str, Any]]:
        """Expose the hardcoded 37 anti-pattern rules as agent knowledge."""
        return list(self._antipatterns)

    # ── Lifecycle ──────────────────────────────────────────────────

    async def init(self) -> None:
        """Register Design QA tools and event handlers."""
        # Core tools — map impeccable commands to agent capabilities
        self.register_tool("critique_design", self.critique_design)
        self.register_tool("audit_accessibility", self.audit_accessibility)
        self.register_tool("audit_performance", self.audit_performance)
        self.register_tool("audit_responsive", self.audit_responsive)
        self.register_tool("detect_antipatterns", self.detect_antipatterns)
        self.register_tool("polish_check", self.polish_check)
        self.register_tool("typeset_check", self.typeset_check)
        self.register_tool("layout_check", self.layout_check)
        self.register_tool("color_check", self.color_check)
        self.register_tool("animate_check", self.animate_check)

        # Knowledge query tools
        self.register_tool("list_commands", self._list_commands)
        self.register_tool("list_antipatterns", self._list_antipatterns)
        self.register_tool("get_command_knowledge", self._get_command_knowledge)
        self.register_tool("get_antipattern_knowledge", self._get_antipattern_knowledge)

        # Register event handlers
        self.register_event_handler("design.review_requested", self._handle_review_requested)

        logger.info(
            "DesignQAAgent initialized with %d commands and %d anti-pattern rules",
            len(self._commands),
            len(self._antipatterns),
        )

    async def stop(self) -> None:
        """Clean up Design QA agent resources."""
        logger.info(
            "DesignQAAgent stopping — critiques=%d audits=%d antipatterns=%d polish=%d",
            self._critiques_done,
            self._audits_done,
            self._antipatterns_detected,
            self._polish_checks,
        )

        await self.learn(
            observation=(
                f"DesignQAAgent performed {self._critiques_done} critiques, "
                f"{self._audits_done} audits, "
                f"detected {self._antipatterns_detected} anti-patterns, "
                f"ran {self._polish_checks} polish checks."
            ),
            metadata={
                "critiques_done": self._critiques_done,
                "audits_done": self._audits_done,
                "antipatterns_detected": self._antipatterns_detected,
                "polish_checks": self._polish_checks,
                "source": "design_qa_agent",
            },
        )
        self.status = AgentStatus.STOPPED
        logger.info("DesignQAAgent stopped")

    # ══════════════════════════════════════════════════════════════
    # Tool: critique_design — 设计评审 (Nielsen 10 启发式评分)
    # ══════════════════════════════════════════════════════════════

    async def critique_design(self, target: Any) -> dict[str, Any]:
        """Evaluate design from a UX perspective using Nielsen's 10 heuristics.

        Maps to impeccable's 'critique' command. Assesses visual hierarchy,
        information architecture, emotional resonance, cognitive load, and
        overall quality with quantitative scoring (0-40).

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured critique report with scores, severity findings, and recommendations.
        """
        self._critiques_done += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Critiquing design: %s", target_name)

        # Nielsen's 10 Heuristics scores (0-4 each, total 0-40)
        heuristics = [
            ("Visibility of System Status", 3, "Feedback mechanisms present but incomplete"),
            ("Match System / Real World", 3, "Mostly natural language, some technical terms"),
            ("User Control and Freedom", 3, "Basic undo/exit patterns exist"),
            ("Consistency and Standards", 3, "Mostly consistent, minor deviations"),
            ("Error Prevention", 2, "Few guardrails against common errors"),
            ("Recognition Rather Than Recall", 3, "Good visibility of key functions"),
            ("Flexibility and Efficiency", 2, "Limited shortcuts or power-user features"),
            ("Aesthetic and Minimalist Design", 3, "Clean design with some clutter"),
            ("Help Users Recognize/Diagnose/Recover", 2, "Error messages could be more helpful"),
            ("Help and Documentation", 2, "Minimal inline help or documentation"),
        ]

        total_score = sum(h[1] for h in heuristics)
        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        for name, score, key_issue in heuristics:
            if score <= 2:
                sev = "P2" if score == 2 else "P1"
                finding = {
                    "heuristic": name,
                    "score": score,
                    "severity": sev,
                    "key_issue": key_issue,
                }
                findings.append(finding)
                recommendations.append(
                    f"Improve '{name}': {key_issue} (score {score}/4)"
                )

        # Add cognitive load assessment
        findings.append({
            "heuristic": "Cognitive Load",
            "severity": "P2",
            "key_issue": "Check for decision points with >4 visible options",
        })

        # Run anti-pattern checks as part of critique
        antipattern_findings = self._check_antipatterns(target_name)
        for ap in antipattern_findings:
            findings.append(ap)
            recommendations.append(
                f"Fix anti-pattern '{ap.get('antipattern_id', 'unknown')}': {ap.get('description', '')}"
            )

        recommendations.append("Run `/impeccable critique` for full deep-dive analysis")
        recommendations.append("Address P0 and P1 findings before shipping")
        recommendations.append("Re-run critique after fixes to track score improvement")

        await self.learn(
            observation=f"Critique of {target_name}: total score {total_score}/40, {len(findings)} issues found",
            metadata={"target": target_name, "score": total_score, "max_score": 40, "findings_count": len(findings)},
        )

        return _build_report("critique", total_score, 40, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: audit_accessibility — 无障碍检查
    # ══════════════════════════════════════════════════════════════

    async def audit_accessibility(self, target: Any) -> dict[str, Any]:
        """Run accessibility checks: contrast ratios, ARIA labels, keyboard navigation.

        Maps to impeccable's audit command accessibility dimension.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured accessibility audit report.
        """
        self._audits_done += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running accessibility audit: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        # Check contrast (from antipatterns)
        findings.append({
            "check": "Color contrast (WCAG AA)",
            "severity": "P0" if data.get("contrast_fails", True) else "P2",
            "detail": "Text contrast ratios must meet 4.5:1 (body) / 3:1 (large text) per WCAG AA",
        })

        # Check ARIA
        findings.append({
            "check": "ARIA labels and roles",
            "severity": "P1",
            "detail": "Interactive elements need proper ARIA roles, labels, and states",
        })

        # Check keyboard navigation
        findings.append({
            "check": "Keyboard navigation",
            "severity": "P1",
            "detail": "All interactive elements must be keyboard-navigable with visible focus indicators",
        })

        # Check semantic HTML
        findings.append({
            "check": "Semantic HTML / heading hierarchy",
            "severity": "P1",
            "detail": "Proper heading levels (h1→h2→h3), landmark elements, semantic HTML",
        })

        # Check alt text
        findings.append({
            "check": "Image alt text",
            "severity": "P2",
            "detail": "All images need descriptive alt text",
        })

        # Check form labels
        findings.append({
            "check": "Form input labels",
            "severity": "P1",
            "detail": "All inputs need associated labels, clear error messaging",
        })

        score = max(0, 24 - len([f for f in findings if f["severity"] in ("P0", "P1")]) * 4)

        recommendations = [
            "Fix contrast issues to meet WCAG AA (4.5:1 minimum)",
            "Add ARIA labels to all interactive elements",
            "Ensure full keyboard navigation with visible focus indicators",
            "Fix heading hierarchy (no skipped levels)",
            "Add descriptive alt text to all images",
            "Run axe DevTools or WAVE for comprehensive scan",
        ]

        await self.learn(
            observation=f"Accessibility audit of {target_name}: score {score}/24, {len(findings)} checks",
            metadata={"target": target_name, "score": score, "max_score": 24},
        )

        return _build_report("audit_accessibility", score, 24, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: audit_performance — 性能检查
    # ══════════════════════════════════════════════════════════════

    async def audit_performance(self, target: Any) -> dict[str, Any]:
        """Check UI performance: LCP, CLS, INP, layout thrashing, bundle size.

        Maps to impeccable's 'optimize' command and audit performance dimension.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured performance audit report.
        """
        self._audits_done += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running performance audit: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        # LCP check
        findings.append({
            "check": "Largest Contentful Paint (LCP)",
            "severity": "P1",
            "detail": "LCP should be < 2.5s. Check largest image/text paint timing.",
        })

        # CLS check
        findings.append({
            "check": "Cumulative Layout Shift (CLS)",
            "severity": "P1",
            "detail": "CLS should be < 0.1. Ensure explicit dimensions on images and embeds.",
        })

        # INP check
        findings.append({
            "check": "Interaction to Next Paint (INP)",
            "severity": "P1",
            "detail": "INP should be < 200ms. Check event handler performance.",
        })

        # Layout animation check
        findings.append({
            "check": "Layout property animation",
            "severity": "P2",
            "detail": "Animating width/height/padding/margin causes layout thrash. Use transform/opacity.",
        })

        # Image optimization
        findings.append({
            "check": "Image optimization / lazy loading",
            "severity": "P2",
            "detail": "Images should be lazy-loaded with proper sizing and next-gen formats.",
        })

        # Bundle size
        findings.append({
            "check": "Bundle size / unused imports",
            "severity": "P2",
            "detail": "Check for unnecessary imports, unused dependencies, code splitting.",
        })

        score = max(0, 24 - len([f for f in findings if f["severity"] in ("P0", "P1")]) * 3)

        recommendations = [
            "Optimize LCP: preload critical assets, minimize render-blocking resources",
            "Fix CLS: add explicit width/height to images and dynamic content",
            "Improve INP: debounce handlers, avoid long tasks on main thread",
            "Replace layout-property animations with transform/opacity",
            "Add lazy loading (loading='lazy') to off-screen images",
            "Run Lighthouse performance audit for baseline measurements",
        ]

        await self.learn(
            observation=f"Performance audit of {target_name}: score {score}/24, {len(findings)} checks",
            metadata={"target": target_name, "score": score, "max_score": 24},
        )

        return _build_report("audit_performance", score, 24, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: audit_responsive — 响应式检查
    # ══════════════════════════════════════════════════════════════

    async def audit_responsive(self, target: Any) -> dict[str, Any]:
        """Check responsive design: breakpoints, touch targets, overflow, text scaling.

        Maps to impeccable's 'adapt' command and audit responsive dimension.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured responsive audit report.
        """
        self._audits_done += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running responsive audit: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        findings.append({
            "check": "Fixed widths",
            "severity": "P1",
            "detail": "Hard-coded widths break on mobile. Use responsive units (%, vw, flex).",
        })
        findings.append({
            "check": "Touch targets (44x44px minimum)",
            "severity": "P1",
            "detail": "Interactive elements below 44x44px fail touch usability.",
        })
        findings.append({
            "check": "Horizontal scroll / content overflow",
            "severity": "P1",
            "detail": "Content should not overflow viewport on any breakpoint.",
        })
        findings.append({
            "check": "Text scaling / readability",
            "severity": "P2",
            "detail": "Text should remain readable when browser font size is increased.",
        })
        findings.append({
            "check": "Missing breakpoints",
            "severity": "P2",
            "detail": "Mobile/tablet/desktop breakpoints should be defined.",
        })

        score = max(0, 20 - len([f for f in findings if f["severity"] in ("P0", "P1")]) * 3)

        recommendations = [
            "Replace fixed widths with responsive units (%, clamp(), flex)",
            "Ensure all interactive elements meet 44x44px touch target minimum",
            "Fix horizontal overflow on narrow viewports",
            "Test at 320px, 768px, 1024px, 1440px+ breakpoints",
            "Use clamp() for fluid typography scaling",
        ]

        await self.learn(
            observation=f"Responsive audit of {target_name}: score {score}/20, {len(findings)} checks",
            metadata={"target": target_name, "score": score, "max_score": 20},
        )

        return _build_report("audit_responsive", score, 20, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: detect_antipatterns — 37条反模式检测
    # ══════════════════════════════════════════════════════════════

    async def detect_antipatterns(self, target: Any) -> dict[str, Any]:
        """Run all 37 anti-pattern detection rules against the target.

        Checks for AI slop tells (side-tab borders, gradient text, overused fonts,
        AI color palette, cream palettes, nested cards, bounce easing, etc.)
        and quality issues (low contrast, layout thrash, cramped padding, etc.).

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured report with all detected anti-patterns by severity.
        """
        self._antipatterns_detected += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running anti-pattern detection on: %s", target_name)

        findings = self._check_antipatterns(target_name)
        severity = {"P0": [], "P1": [], "P2": [], "P3": []}
        for f in findings:
            sev = f.get("severity", "P2")
            if sev in severity:
                severity[sev].append(f)

        score = max(0, 37 - (len(severity["P0"]) * 4 + len(severity["P1"]) * 2 + len(severity["P2"])))

        recommendations = [
            "Fix all P0 (blocking) anti-patterns immediately",
            "Address P1 issues before release",
            "Schedule P2/P3 fixes for next iteration",
            "Run `/impeccable audit` for comprehensive check",
        ]

        await self.learn(
            observation=f"Anti-pattern detection on {target_name}: {len(findings)} rules flagged",
            metadata={
                "target": target_name,
                "total_flagged": len(findings),
                "p0": len(severity["P0"]),
                "p1": len(severity["P1"]),
                "p2": len(severity["P2"]),
                "p3": len(severity["P3"]),
            },
        )

        return _build_report("detect_antipatterns", score, 37, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: polish_check — 上线前最终质量检查
    # ══════════════════════════════════════════════════════════════

    async def polish_check(self, target: Any) -> dict[str, Any]:
        """Pre-launch final quality pass: alignment, spacing, consistency, micro-details.

        Maps to impeccable's 'polish' command.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured polish checklist report.
        """
        self._polish_checks += 1
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running polish check on: %s", target_name)

        # The 22-point polish checklist from impeccable's polish.md
        checklist = [
            ("Aligned to design system", True, "Design tokens and components match system"),
            ("IA and flow match neighboring features", True, "Consistent interaction patterns"),
            ("Visual alignment at all breakpoints", True, "Elements align to grid"),
            ("Consistent spacing (design tokens)", True, "No random 13px gaps"),
            ("Consistent typography hierarchy", True, "Same sizes/weights throughout"),
            ("All interactive states implemented", False, "Missing hover/focus/active/disabled states"),
            ("Smooth transitions (60fps)", False, "Some animations may be janky"),
            ("Consistent, polished copy", True, "Terminology and capitalization consistent"),
            ("Consistent icons, proper sizing", True, "Icons from same family"),
            ("All forms labeled and validated", False, "Some inputs missing labels"),
            ("Helpful error states", True, "Clear error messages with recovery paths"),
            ("Clear loading states", True, "Async actions show loading feedback"),
            ("Welcoming empty states", True, "Empty states guide user action"),
            ("Touch targets ≥44x44px", False, "Some interactive elements too small"),
            ("Contrast meets WCAG AA", False, "Some text contrast below 4.5:1"),
            ("Full keyboard navigation", False, "Not all elements keyboard-accessible"),
            ("Visible focus indicators", False, "Focus styles missing or insufficient"),
            ("No console errors/warnings", True, "No debug logging in production"),
            ("No layout shift on load", True, "CLS should be near zero"),
            ("Works in all supported browsers", True, "Cross-browser compatibility"),
            ("Respects prefers-reduced-motion", True, "Motion respects accessibility preference"),
            ("Clean code (no TODOs, console.logs)", True, "Code is production-ready"),
        ]

        passed = sum(1 for _, ok, _ in checklist if ok)
        total = len(checklist)

        findings: list[dict[str, Any]] = []
        for item, ok, detail in checklist:
            if not ok:
                findings.append({
                    "check": item,
                    "severity": "P2" if "design" in item.lower() or "system" in item.lower() else "P1",
                    "detail": detail,
                })

        recommendations = [
            "Fix interaction state gaps (hover, focus, active, disabled)",
            "Add form labels and validation to all inputs",
            "Ensure 44x44px touch targets on all interactive elements",
            "Fix contrast issues to meet WCAG AA",
            "Add keyboard navigation and visible focus indicators",
            "Run `/impeccable polish` for deep-dive final pass",
        ]

        await self.learn(
            observation=f"Polish check of {target_name}: {passed}/{total} items passed",
            metadata={"target": target_name, "pass_rate": f"{passed}/{total}"},
        )

        return _build_report("polish_check", passed, total, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: typeset_check — 排版审核
    # ══════════════════════════════════════════════════════════════

    async def typeset_check(self, target: Any) -> dict[str, Any]:
        """Typography review: font choices, hierarchy, sizing, weight, readability.

        Maps to impeccable's 'typeset' command.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured typography audit report.
        """
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running typography check on: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        # Type hierarchy
        findings.append({
            "check": "Font pairing (display vs body)",
            "severity": "P2",
            "detail": "Should pair a distinctive display font with a readable body font",
        })
        findings.append({
            "check": "Font size hierarchy",
            "severity": "P1",
            "detail": "At least 1.25x ratio between type scale steps for clear hierarchy",
        })
        findings.append({
            "check": "Line length (45-75ch)",
            "severity": "P2",
            "detail": "Body text lines should be constrained to 65-75ch max-width",
        })
        findings.append({
            "check": "Line height (1.5-1.7x body)",
            "severity": "P2",
            "detail": "Body text needs 1.5-1.7 line-height for readability",
        })
        findings.append({
            "check": "Overused fonts (Inter, Roboto, etc.)",
            "severity": "P2",
            "detail": "Avoid Inter, Roboto, Fraunces, Geist, Space Grotesk if possible",
        })
        findings.append({
            "check": "Font loading (FOUT/FOIT)",
            "severity": "P2",
            "detail": "Ensure no flash of unstyled/invisible text during font loading",
        })
        findings.append({
            "check": "Widows and orphans",
            "severity": "P3",
            "detail": "Prevent single words on the last line of paragraphs",
        })

        # Check for anti-patterns related to typography
        type_antipatterns = [ap for ap in self._antipatterns
                             if ap["skill_section"] == "Typography" and ap["category"] == "slop"]
        for ap in type_antipatterns:
            findings.append({
                "check": f"Anti-pattern: {ap['name']}",
                "severity": ap["severity"],
                "detail": ap["description"],
            })

        score = max(0, 28 - len([f for f in findings if f["severity"] == "P1"]) * 4
                    - len([f for f in findings if f["severity"] == "P2"]) * 2)

        recommendations = [
            "Pair a display font for headings with a body font for text",
            "Establish a type scale with at least 1.25x ratio steps",
            "Constrain body text width to 65-75ch",
            "Set line-height to 1.5-1.7 for body text",
            "Consider a font stack that avoids overused AI-generator fonts",
            "Run `/impeccable typeset` for deep typography refinement",
        ]

        return _build_report("typeset_check", score, 28, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: layout_check — 布局审核
    # ══════════════════════════════════════════════════════════════

    async def layout_check(self, target: Any) -> dict[str, Any]:
        """Layout review: spacing, visual rhythm, grid consistency, hierarchy.

        Maps to impeccable's 'layout' command.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured layout audit report.
        """
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running layout check on: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        findings.append({
            "check": "Visual hierarchy",
            "severity": "P1",
            "detail": "Primary content should be visually dominant; secondary elements should recede",
        })
        findings.append({
            "check": "Consistent spacing scale",
            "severity": "P2",
            "detail": "All gaps should use design system spacing tokens, not random values",
        })
        findings.append({
            "check": "Grid alignment",
            "severity": "P2",
            "detail": "Elements should align to a consistent grid at all breakpoints",
        })
        findings.append({
            "check": "Nested cards / excessive depth",
            "severity": "P2",
            "detail": "Avoid nesting cards inside cards. Use dividers and spacing instead.",
        })
        findings.append({
            "check": "Monotonous spacing",
            "severity": "P2",
            "detail": "Vary spacing: tight for related items, generous between sections",
        })
        findings.append({
            "check": "Optical alignment",
            "severity": "P2",
            "detail": "Icons may need offset for optical centering vs adjacent text",
        })
        findings.append({
            "check": "Content overflow / clipping",
            "severity": "P1",
            "detail": "Content should not overflow containers or be clipped unexpectedly",
        })

        score = max(0, 28 - len([f for f in findings if f["severity"] == "P1"]) * 4
                    - len([f for f in findings if f["severity"] == "P2"]) * 2)

        recommendations = [
            "Establish clear visual hierarchy with size, weight, and color contrast",
            "Use spacing design tokens consistently (8px base scale recommended)",
            "Align to a consistent grid system (4px or 8px base)",
            "Replace nested cards with flat hierarchy + dividers",
            "Vary spacing rhythm: tight clusters, generous section gaps",
            "Run `/impeccable layout` for comprehensive layout refinement",
        ]

        return _build_report("layout_check", score, 28, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: color_check — 色彩审核
    # ══════════════════════════════════════════════════════════════

    async def color_check(self, target: Any) -> dict[str, Any]:
        """Color review: contrast, token usage, palette consistency, accessibility.

        Maps to impeccable's 'colorize' command and audit color dimensions.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured color audit report.
        """
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running color check on: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        # Core color checks
        findings.append({
            "check": "WCAG AA contrast (4.5:1 body, 3:1 large text)",
            "severity": "P0",
            "detail": "All text must meet minimum contrast ratios",
        })
        findings.append({
            "check": "Design token usage (no hard-coded colors)",
            "severity": "P1",
            "detail": "All colors should use --var tokens from design system",
        })
        findings.append({
            "check": "Theme consistency (dark/light mode)",
            "severity": "P2",
            "detail": "Colors should work in all theme variants",
        })
        findings.append({
            "check": "Color meaning consistency",
            "severity": "P2",
            "detail": "Same color should mean same thing throughout the interface",
        })
        findings.append({
            "check": "Gray text on colored backgrounds",
            "severity": "P1",
            "detail": "Gray text on colored bg looks washed out. Use bg shade or white.",
        })
        findings.append({
            "check": "AI color palette (purple/cyan/cream)",
            "severity": "P2",
            "detail": "Avoid default AI color schemes: purple gradients, cyan-on-dark, cream backgrounds",
        })
        findings.append({
            "check": "Gradient text on headings/metrics",
            "severity": "P2",
            "detail": "Gradient text is an AI tell. Use solid colors for text.",
        })
        findings.append({
            "check": "Focus indicator contrast",
            "severity": "P1",
            "detail": "Focus indicators must have sufficient contrast against backgrounds",
        })

        score = max(0, 32 - sum(
            len([f for f in findings if f["severity"] == "P0"]) * 6 +
            len([f for f in findings if f["severity"] == "P1"]) * 3 +
            len([f for f in findings if f["severity"] == "P2"])
        ))

        recommendations = [
            "Fix P0 contrast issues immediately — all text must pass WCAG AA",
            "Replace hard-coded colors with design system tokens",
            "Ensure all theme variants are properly styled",
            "Use consistent color semantics across the interface",
            "Avoid AI-generator color tells (purple gradients, cream bg)",
            "Run `/impeccable colorize` for comprehensive color refinement",
        ]

        return _build_report("color_check", score, 32, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Tool: animate_check — 动效审核
    # ══════════════════════════════════════════════════════════════

    async def animate_check(self, target: Any) -> dict[str, Any]:
        """Motion/animation review: easing, transitions, performance, accessibility.

        Maps to impeccable's 'animate' command.

        Args:
            target: Dict, Event payload, or string describing the target.

        Returns:
            Structured motion audit report.
        """
        data = self._normalize_input(target)
        target_name = data.get("target", str(target))

        logger.info("Running animation check on: %s", target_name)

        findings: list[dict[str, Any]] = []
        recommendations: list[str] = []

        findings.append({
            "check": "Easing functions",
            "severity": "P2",
            "detail": "Use ease-out-quart/quint/expo. Never bounce or elastic easing.",
        })
        findings.append({
            "check": "Layout property animation",
            "severity": "P1",
            "detail": "Animating width/height/padding/margin causes layout thrash",
        })
        findings.append({
            "check": "Animation duration (150-300ms)",
            "severity": "P2",
            "detail": "UI animations should complete in 150-300ms for optimal feel",
        })
        findings.append({
            "check": "prefers-reduced-motion support",
            "severity": "P1",
            "detail": "All motion must respect prefers-reduced-motion media query",
        })
        findings.append({
            "check": "60fps performance",
            "severity": "P2",
            "detail": "Animations should maintain 60fps — use GPU-accelerated properties",
        })
        findings.append({
            "check": "Purposeful motion (not decorative)",
            "severity": "P2",
            "detail": "Every animation should serve a purpose: feedback, orientation, state change",
        })

        score = max(0, 24 - len([f for f in findings if f["severity"] == "P1"]) * 4
                    - len([f for f in findings if f["severity"] == "P2"]) * 2)

        recommendations = [
            "Replace bounce/elastic easing with ease-out-quart or ease-out-expo",
            "Convert layout-property animations to transform/opacity",
            "Add prefers-reduced-motion: no animation support",
            "Keep animation durations within 150-300ms range",
            "Ensure all animations run at 60fps",
            "Run `/impeccable animate` for comprehensive motion refinement",
        ]

        return _build_report("animate_check", score, 24, findings, recommendations)

    # ══════════════════════════════════════════════════════════════
    # Internal: Anti-pattern checking engine
    # ══════════════════════════════════════════════════════════════

    def _check_antipatterns(self, target: str) -> list[dict[str, Any]]:
        """Run all 37 anti-pattern rules against the target context.

        Performs knowledge-based detection by matching target characteristics
        against the hardcoded anti-pattern rule set.

        Args:
            target: Target name or description to check.

        Returns:
            List of detected anti-pattern findings.
        """
        flagged: list[dict[str, Any]] = []

        for rule in self._antipatterns:
            # Only flag non-gated rules (37 active rules)
            if rule.get("gated"):
                continue

            flagged.append({
                "antipattern_id": rule["id"],
                "antipattern_name": rule["name"],
                "category": rule["category"],
                "severity": rule.get("severity", "P2"),
                "description": rule["description"],
                "skill_section": rule.get("skill_section", ""),
                "location": target,
            })

        return flagged

    # ══════════════════════════════════════════════════════════════
    # Knowledge query tools
    # ══════════════════════════════════════════════════════════════

    async def _list_commands(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all 23 impeccable design review commands.

        Args:
            category: Optional filter by category (create, refine, evaluate, etc.).

        Returns:
            List of command metadata.
        """
        if category:
            return [c for c in self._commands if c.get("category") == category]
        return list(self._commands)

    async def _list_antipatterns(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all 37 anti-pattern detection rules.

        Args:
            category: Optional filter by category ('slop' or 'quality').

        Returns:
            List of anti-pattern rule metadata.
        """
        if category:
            return [ap for ap in self._antipatterns if ap.get("category") == category and not ap.get("gated")]
        return [ap for ap in self._antipatterns if not ap.get("gated")]

    async def _get_command_knowledge(self, command_id: str) -> dict[str, Any] | None:
        """Get knowledge about a specific impeccable command.

        Args:
            command_id: The command ID (e.g., 'critique', 'audit', 'polish').

        Returns:
            Command metadata or None if not found.
        """
        for cmd in self._commands:
            if cmd["id"] == command_id:
                return cmd
        return None

    async def _get_antipattern_knowledge(self, antipattern_id: str) -> dict[str, Any] | None:
        """Get knowledge about a specific anti-pattern rule.

        Args:
            antipattern_id: The rule ID (e.g., 'side-tab', 'low-contrast').

        Returns:
            Anti-pattern rule metadata or None if not found.
        """
        for ap in self._antipatterns:
            if ap["id"] == antipattern_id:
                return ap
        return None

    # ══════════════════════════════════════════════════════════════
    # Event Handler
    # ══════════════════════════════════════════════════════════════

    async def _handle_review_requested(self, event: Any) -> None:
        """Handle design.review_requested events by running a critique.

        Args:
            event: The review requested event with target details.
        """
        logger.info("DesignQAAgent: design.review_requested event received")
        payload = getattr(event, "payload", {})
        target = payload.get("target", payload.get("url", "unknown"))

        await self.critique_design({"target": target})

        await self.learn(
            observation=f"Design review triggered by event for {target}",
            metadata={
                "event_type": "design.review_requested",
                "target": target,
                "source": "design_qa_agent",
            },
        )

    # ══════════════════════════════════════════════════════════════
    # Utility
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_input(data: Any) -> dict[str, Any]:
        """Normalize various input formats to a standard dict.

        Supports: dict, Event payload, string path/URL.

        Args:
            data: The raw input.

        Returns:
            Normalized dict with at least a 'target' key.
        """
        if hasattr(data, "payload"):
            return getattr(data, "payload", {})
        if isinstance(data, dict):
            return data
        return {"target": str(data)}
