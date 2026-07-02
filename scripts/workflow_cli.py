from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = "待补充"


@dataclass
class InitBookInput:
    title: str
    genre: str
    platform: str
    hook: str
    protagonist: str
    length: str
    tone: str | None
    reference: str | None
    codename: str | None
    root: Path
    force: bool


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    command = args.command

    if command == "init-book":
        return run_init_book(
            InitBookInput(
                title=args.title,
                genre=args.genre,
                platform=args.platform,
                hook=args.hook,
                protagonist=args.protagonist,
                length=args.length,
                tone=args.tone,
                reference=args.reference,
                codename=args.codename,
                root=Path(args.root).resolve(),
                force=args.force,
            )
        )
    if command == "init-state":
        return run_init_state(Path(args.root).resolve(), force=args.force)
    if command == "plan-chapter":
        return run_plan_chapter(args)
    if command == "record-review":
        return run_record_review(args)
    if command == "prompt-chapter":
        return run_prompt_chapter(args)
    if command == "draft-chapter":
        return run_draft_chapter(args)
    if command == "humanize-chapter":
        return run_humanize_chapter(args)
    if command == "review-draft":
        return run_review_draft(args)
    if command == "sync-state":
        return run_sync_state(args)
    if command == "render-artifacts":
        return run_render_artifacts(args)

    print(f"未知命令: {command}", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workflow-cli",
        description="writer-system workflow command runner",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-book", help="初始化一本新书")
    add_root_arg(init_parser)
    init_parser.add_argument("--title", required=True, help="书名")
    init_parser.add_argument("--genre", required=True, help="题材")
    init_parser.add_argument("--platform", required=True, help="目标平台")
    init_parser.add_argument("--hook", required=True, help="核心卖点")
    init_parser.add_argument("--protagonist", required=True, help="主角名称或定位")
    init_parser.add_argument("--length", required=True, help="目标篇幅")
    init_parser.add_argument("--tone", help="文风偏好")
    init_parser.add_argument("--reference", help="参考作品或风格")
    init_parser.add_argument("--codename", help="项目代称")
    init_parser.add_argument("--force", action="store_true", help="覆盖非占位文件")

    init_state_parser = subparsers.add_parser("init-state", help="补齐结构化状态")
    add_root_arg(init_state_parser)
    init_state_parser.add_argument("--force", action="store_true", help="覆盖非占位文件")

    plan_parser = subparsers.add_parser("plan-chapter", help="生成章节计划")
    add_root_arg(plan_parser)
    add_chapter_arg(plan_parser)
    plan_parser.add_argument("--title", help="章节标题")
    plan_parser.add_argument("--volume", default="第一卷", help="所属卷")
    plan_parser.add_argument("--goal", help="本章目标")
    plan_parser.add_argument("--brief-text", help="章节输入简报文本")
    plan_parser.add_argument("--brief-file", help="章节输入简报文件路径")
    plan_parser.add_argument("--target-words", type=int, default=3000, help="目标字数")
    plan_parser.add_argument("--ending-type", default="钩子推进", help="章末落点类型")
    plan_parser.add_argument("--must-payoff", action="append", default=[], help="必须处理的伏笔 ID，可重复传入")
    plan_parser.add_argument("--force", action="store_true", help="覆盖已有计划文件")

    human_review_parser = subparsers.add_parser("record-review", help="记录人工审核结论")
    add_root_arg(human_review_parser)
    add_chapter_arg(human_review_parser)
    human_review_parser.add_argument("--stage", choices=["plan", "final"], required=True, help="审核阶段")
    human_review_parser.add_argument(
        "--decision",
        choices=["approved", "changes_requested", "rejected"],
        required=True,
        help="审核结论",
    )
    human_review_parser.add_argument("--reviewer", default="human", help="审核人标识")
    human_review_parser.add_argument("--notes", default="", help="审核备注")
    human_review_parser.add_argument("--source-file", help="可选，记录对应文件路径")
    human_review_parser.add_argument("--force", action="store_true", help="覆盖已有审核记录")

    prompt_parser = subparsers.add_parser("prompt-chapter", help="生成正文骨架 / 提示词")
    add_root_arg(prompt_parser)
    add_chapter_arg(prompt_parser)
    prompt_parser.add_argument("--force", action="store_true", help="覆盖已有 prompt 文件")

    draft_parser = subparsers.add_parser("draft-chapter", help="生成正文初稿")
    add_root_arg(draft_parser)
    add_chapter_arg(draft_parser)
    draft_parser.add_argument("--force", action="store_true", help="覆盖已有初稿文件")

    humanize_parser = subparsers.add_parser("humanize-chapter", help="修订正文初稿")
    add_root_arg(humanize_parser)
    add_chapter_arg(humanize_parser)
    humanize_parser.add_argument("--source-file", help="指定草稿文件路径")
    humanize_parser.add_argument("--force", action="store_true", help="覆盖已有修订稿")

    review_parser = subparsers.add_parser("review-draft", help="生成正文审查报告")
    add_root_arg(review_parser)
    add_chapter_arg(review_parser)
    review_parser.add_argument("--draft-file", help="指定待审查草稿文件路径")
    review_parser.add_argument("--force", action="store_true", help="覆盖已有审稿报告")

    sync_parser = subparsers.add_parser("sync-state", help="同步结构化状态")
    add_root_arg(sync_parser)
    add_chapter_arg(sync_parser)
    sync_parser.add_argument("--final-file", help="指定正式版本路径")
    sync_parser.add_argument("--force", action="store_true", help="覆盖已有状态差异报告")

    render_parser = subparsers.add_parser("render-artifacts", help="渲染回顾产物")
    add_root_arg(render_parser)
    render_parser.add_argument("--chapter", type=int, help="可选，指出最近更新章节")
    render_parser.add_argument("--force", action="store_true", help="覆盖已有 recap 文件")

    return parser


def add_root_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="目标仓库根目录，默认当前 writer-system 根目录",
    )


def add_chapter_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--chapter", type=int, required=True, help="章节号，例如 1 或 12")


def run_init_book(data: InitBookInput) -> int:
    target_root = data.root
    ensure_book_dirs(target_root)

    codename = data.codename or data.title
    tone = data.tone or PLACEHOLDER
    reference = data.reference or PLACEHOLDER

    files: list[tuple[Path, str]] = [
        (target_root / "book" / "canon" / "premise.md", render_premise_md(data)),
        (target_root / "book" / "canon" / "setting.md", render_setting_md(data)),
        (target_root / "book" / "canon" / "style_rules.md", render_style_rules_md(data)),
        (target_root / "book" / "canon" / "characters" / "protagonist.md", render_protagonist_md(data)),
        (target_root / "book" / "canon" / "volumes" / "volume-01-outline.md", render_volume_outline_md(data)),
        (target_root / "book" / "state" / "characters.yaml", render_characters_yaml(data)),
        (target_root / "book" / "state" / "factions.yaml", render_factions_yaml()),
        (target_root / "book" / "state" / "foreshadows.yaml", "[]\n"),
        (target_root / "book" / "state" / "power_state.yaml", render_power_state_yaml(data)),
        (target_root / "book" / "state" / "chapter_index.yaml", "[]\n"),
        (
            target_root / "book" / "artifacts" / "reports" / "init-book-summary.md",
            render_init_summary_md(data, codename=codename, tone=tone, reference=reference),
        ),
    ]

    written, skipped = write_files(files, force=data.force)
    print_write_summary("init-book", target_root, written, skipped)
    return 0 if written else 1


def run_init_state(root: Path, force: bool) -> int:
    ensure_book_dirs(root)
    protagonist_name = extract_protagonist_name(root) or PLACEHOLDER
    hook = extract_hook(root) or PLACEHOLDER
    pseudo = InitBookInput(
        title=extract_book_title(root) or "待命名作品",
        genre=extract_genre(root) or PLACEHOLDER,
        platform=extract_platform(root) or PLACEHOLDER,
        hook=hook,
        protagonist=protagonist_name,
        length="待补充",
        tone=None,
        reference=None,
        codename=None,
        root=root,
        force=force,
    )

    files = [
        (root / "book" / "state" / "characters.yaml", render_characters_yaml(pseudo)),
        (root / "book" / "state" / "factions.yaml", render_factions_yaml()),
        (root / "book" / "state" / "foreshadows.yaml", "[]\n"),
        (root / "book" / "state" / "power_state.yaml", render_power_state_yaml(pseudo)),
        (root / "book" / "state" / "chapter_index.yaml", "[]\n"),
    ]
    written, skipped = write_files(files, force=force)
    print_write_summary("init-state", root, written, skipped)
    return 0 if written else 1


def run_plan_chapter(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    chapter_dir.mkdir(parents=True, exist_ok=True)

    state_ready = state_is_ready_for_planning(root)
    if not state_ready[0]:
        print(f"plan-chapter 无法执行：{state_ready[1]}", file=sys.stderr)
        return 1

    protagonist_name = extract_protagonist_name(root) or "主角"
    brief_text = load_brief_text(args)
    brief_data = parse_brief_text(brief_text) if brief_text else {}
    chapter_title = args.title or brief_data.get("title") or f"第{args.chapter}章待定标题"
    chapter_goal = args.goal or brief_data.get("goal") or f"推进《{chapter_title}》的核心冲突"
    volume = brief_data.get("volume") or args.volume
    target_words = int(brief_data.get("target_words") or args.target_words)
    ending_type = brief_data.get("ending_type") or args.ending_type
    must_payoff_ids = args.must_payoff or select_open_foreshadows(root)
    brief_must_nodes = brief_data.get("must_nodes", [])
    brief_risks = brief_data.get("risks", [])
    ending_hint = brief_data.get("ending") or "为下一章留下清晰承接点"
    beat_suggestions = brief_data.get("beat_suggestions", [])

    beats = build_beats(
        protagonist_name=protagonist_name,
        chapter_title=chapter_title,
        chapter_goal=chapter_goal,
        target_words=target_words,
        beat_suggestions=beat_suggestions,
        ending_type=ending_type,
    )
    plan_data = {
        "chapter": args.chapter,
        "title": chapter_title,
        "volume": volume,
        "goal": chapter_goal,
        "target_words": target_words,
        "ending_type": ending_type,
        "ending_hint": ending_hint,
        "must_payoff_ids": must_payoff_ids,
        "must_nodes": brief_must_nodes or [
            f"{protagonist_name}必须正式进入本章核心冲突",
            "本章关键矛盾必须完成至少一次实质推进",
            f"结尾必须形成“{ending_type}”的明确落点",
        ],
        "state_constraints": build_state_constraints(root),
        "risks": brief_risks or [
            "避免目标不清导致节拍重复推进",
            "避免核心冲突出场过晚导致前摇过长",
            "避免章末落点提前透支下一章主内容",
        ],
        "beats": beats,
    }

    plan_md = render_plan_markdown(plan_data)
    plan_path = chapter_dir / "plan.md"
    plan_yaml_path = chapter_dir / "plan.data.yaml"
    report_path = root / "book" / "artifacts" / "reports" / f"chapter-{format_chapter(args.chapter)}-plan-check.md"
    files = [
        (plan_path, plan_md),
        (plan_yaml_path, dump_yaml(plan_data)),
        (report_path, render_plan_check_md(plan_data)),
    ]
    if brief_text:
        files.append((chapter_dir / "brief.md", brief_text))

    written, skipped = write_files(files, force=args.force)
    print_write_summary("plan-chapter", root, written, skipped)
    return 0 if written else 1


def run_record_review(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    chapter_dir.mkdir(parents=True, exist_ok=True)
    review_path = get_human_review_path(chapter_dir, args.stage)

    if args.stage == "plan":
        plan_data = load_plan_data(chapter_dir)
        if not plan_data:
            print("record-review 无法执行：缺少 plan.data.yaml。", file=sys.stderr)
            return 1
        title = plan_data["title"]
        source_name = Path(args.source_file).name if args.source_file else "plan.md"
    else:
        final_path = Path(args.source_file).resolve() if args.source_file else chapter_dir / "final.md"
        if not final_path.exists():
            print("record-review 无法执行：final 阶段需要已存在的正式版本文件。", file=sys.stderr)
            return 1
        plan_data = load_plan_data(chapter_dir) or {}
        title = plan_data.get("title", f"第{args.chapter}章")
        source_name = final_path.name

    decision_map = {
        "approved": "通过",
        "changes_requested": "需修改",
        "rejected": "拒绝",
    }
    reviewed_at = datetime.now().isoformat(timespec="seconds")
    payload = {
        "chapter": args.chapter,
        "stage": args.stage,
        "decision": args.decision,
        "decision_label": decision_map[args.decision],
        "reviewer": args.reviewer,
        "reviewed_at": reviewed_at,
        "source_file": source_name,
        "notes": args.notes.strip(),
    }
    report_path = root / "book" / "artifacts" / "reports" / f"chapter-{format_chapter(args.chapter)}-{args.stage}-human-review.md"
    files = [
        (review_path, dump_yaml(payload)),
        (report_path, render_human_review_md(payload, title=title)),
    ]
    written, skipped = write_files(files, force=args.force)
    print_write_summary("record-review", root, written, skipped)
    return 0 if written else 1


def run_prompt_chapter(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    plan_data = load_plan_data(chapter_dir)
    if not plan_data:
        print("prompt-chapter 无法执行：缺少 plan.data.yaml，请先执行 plan-chapter。", file=sys.stderr)
        return 1
    plan_gate = require_human_review_approval(chapter_dir, "plan")
    if not plan_gate[0]:
        print(f"prompt-chapter 无法执行：{plan_gate[1]}", file=sys.stderr)
        return 1

    protagonist_name = extract_protagonist_name(root) or "主角"
    book_title = extract_book_title(root) or "待命名作品"
    genre = extract_genre(root) or "待补充题材"
    platform = extract_platform(root) or "待补充平台"
    hook = extract_hook(root) or "待补充核心卖点"
    style_rules = extract_style_rules_summary(root)
    state_constraints = plan_data.get("state_constraints", {})
    previous_context = load_previous_context(root, args.chapter)
    chapter_mode = infer_chapter_mode(plan_data["goal"], plan_data["beats"], plan_data.get("ending_type", "待补充"))
    key_characters = collect_key_characters(root, protagonist_name)
    key_factions = collect_key_factions(root)
    key_foreshadows = collect_key_foreshadows(root, plan_data.get("must_payoff_ids", []))
    power_snapshot = collect_power_snapshot(root)
    taboos = collect_taboos(root, plan_data.get("risks", []))

    prompt_md = render_prompt_markdown(
        book_title=book_title,
        chapter=args.chapter,
        title=plan_data["title"],
        volume=plan_data["volume"],
        genre=genre,
        platform=platform,
        hook=hook,
        chapter_mode=chapter_mode,
        protagonist_name=protagonist_name,
        goal=plan_data["goal"],
        target_words=int(plan_data.get("target_words", 3000)),
        beats=plan_data["beats"],
        must_nodes=plan_data.get("must_nodes", []),
        style_rules=style_rules,
        state_constraints=state_constraints,
        ending_type=plan_data.get("ending_type", "待补充"),
        ending_hint=plan_data.get("ending_hint", "待补充"),
        previous_context=previous_context,
        key_characters=key_characters,
        key_factions=key_factions,
        key_foreshadows=key_foreshadows,
        power_snapshot=power_snapshot,
        taboos=taboos,
    )
    prompt_data = {
        "book_title": book_title,
        "chapter": args.chapter,
        "title": plan_data["title"],
        "volume": plan_data["volume"],
        "genre": genre,
        "platform": platform,
        "hook": hook,
        "chapter_mode": chapter_mode,
        "protagonist_name": protagonist_name,
        "goal": plan_data["goal"],
        "target_words": int(plan_data["target_words"]),
        "source_plan": "plan.data.yaml",
        "ending_type": plan_data.get("ending_type"),
        "ending_hint": plan_data.get("ending_hint", "待补充"),
        "previous_context": previous_context,
        "beats": plan_data["beats"],
        "must_nodes": plan_data.get("must_nodes", []),
        "must_payoff_ids": plan_data.get("must_payoff_ids", []),
        "style_rules": style_rules,
        "state_constraints": state_constraints,
        "key_characters": key_characters,
        "key_factions": key_factions,
        "key_foreshadows": key_foreshadows,
        "power_snapshot": power_snapshot,
        "taboos": taboos,
        "risks": plan_data.get("risks", []),
    }
    written, skipped = write_files(
        [
            (chapter_dir / "prompt.md", prompt_md),
            (chapter_dir / "prompt.data.yaml", dump_yaml(prompt_data)),
        ],
        force=args.force,
    )
    print_write_summary("prompt-chapter", root, written, skipped)
    return 0 if written else 1


def run_draft_chapter(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    plan_gate = require_human_review_approval(chapter_dir, "plan")
    if not plan_gate[0]:
        print(f"draft-chapter 无法执行：{plan_gate[1]}", file=sys.stderr)
        return 1
    prompt_data = load_yaml(chapter_dir / "prompt.data.yaml")
    prompt_path = chapter_dir / "prompt.md"
    if not prompt_data or not prompt_path.exists():
        print("draft-chapter 无法执行：缺少 prompt.md / prompt.data.yaml，请先执行 prompt-chapter。", file=sys.stderr)
        return 1

    protagonist_name = prompt_data.get("protagonist_name") or extract_protagonist_name(root) or "主角"
    title = prompt_data["title"]
    goal = prompt_data["goal"]
    ending_type = prompt_data.get("ending_type", "待补充")
    ending_hint = prompt_data.get("ending_hint", "待补充")
    previous_context = prompt_data.get("previous_context", "上一章上下文待补充。")
    beats = prompt_data.get("beats") or []
    style_rules = prompt_data.get("style_rules") or []
    key_foreshadows = prompt_data.get("key_foreshadows") or []
    power_snapshot = prompt_data.get("power_snapshot") or []
    must_nodes = prompt_data.get("must_nodes") or []
    draft_text = render_offline_draft_markdown(
        chapter=args.chapter,
        title=title,
        protagonist_name=protagonist_name,
        goal=goal,
        previous_context=previous_context,
        beats=beats,
        must_nodes=must_nodes,
        style_rules=style_rules,
        key_foreshadows=key_foreshadows,
        power_snapshot=power_snapshot,
        ending_type=ending_type,
        ending_hint=ending_hint,
    )

    draft_path = chapter_dir / "draft-v1.md"
    draft_data_path = chapter_dir / "draft-v1.data.yaml"
    metadata = {
        "chapter": args.chapter,
        "title": title,
        "source_prompt": "prompt.md",
        "version": "draft-v1",
        "beat_count": len(beats),
        "target_words": int(prompt_data.get("target_words", 0)),
    }
    written, skipped = write_files(
        [(draft_path, draft_text), (draft_data_path, dump_yaml(metadata))],
        force=args.force,
    )
    print_write_summary("draft-chapter", root, written, skipped)
    return 0 if written else 1


def run_humanize_chapter(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    plan_gate = require_human_review_approval(chapter_dir, "plan")
    if not plan_gate[0]:
        print(f"humanize-chapter 无法执行：{plan_gate[1]}", file=sys.stderr)
        return 1
    source_path = Path(args.source_file).resolve() if args.source_file else detect_latest_draft(chapter_dir)
    if not source_path or not source_path.exists():
        print("humanize-chapter 无法执行：找不到草稿文件。", file=sys.stderr)
        return 1

    text = source_path.read_text(encoding="utf-8")
    text = clean_prompt_leakage(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = split_long_lines(text)
    text = normalize_dialogue_spacing(text)
    text = text.strip() + "\n"

    target_path = chapter_dir / "draft-v2-humanized.md"
    meta_path = chapter_dir / "draft-v2-humanized.data.yaml"
    metadata = {
        "chapter": args.chapter,
        "source_file": source_path.name,
        "version": "draft-v2-humanized",
    }
    written, skipped = write_files(
        [(target_path, text), (meta_path, dump_yaml(metadata))],
        force=args.force,
    )
    print_write_summary("humanize-chapter", root, written, skipped)
    return 0 if written else 1


def run_review_draft(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    plan_gate = require_human_review_approval(chapter_dir, "plan")
    if not plan_gate[0]:
        print(f"review-draft 无法执行：{plan_gate[1]}", file=sys.stderr)
        return 1
    draft_path = Path(args.draft_file).resolve() if args.draft_file else detect_review_target(chapter_dir)
    if not draft_path or not draft_path.exists():
        print("review-draft 无法执行：找不到待审稿文件。", file=sys.stderr)
        return 1

    plan_data = load_plan_data(chapter_dir)
    if not plan_data:
        print("review-draft 无法执行：缺少 plan.data.yaml。", file=sys.stderr)
        return 1

    text = draft_path.read_text(encoding="utf-8")
    blockers: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if PLACEHOLDER in text:
        blockers.append("正文中仍存在“待补充”，说明草稿尚未完成。")
    if not text.lstrip().startswith("# 第"):
        blockers.append("正文缺少明确章节标题。")
    leakage_markers = detect_prompt_leakage_markers(text)
    if leakage_markers:
        blockers.append(f"正文仍残留提示词/元数据结构：{', '.join(leakage_markers[:6])}")
    if not looks_like_narrative_prose(text):
        blockers.append("正文主体缺少连续叙事场景，当前更像提示词说明而不是小说正文。")

    for must_node in plan_data.get("must_nodes", []):
        keyword = meaningful_fragment(must_node)
        if keyword and keyword not in text:
            warnings.append(f"必写节点可能未充分落地：{must_node}")

    if plan_data.get("ending_type") not in text:
        warnings.append(f"章末落点未明显体现计划中的类型：{plan_data.get('ending_type')}")

    word_count = count_cjk_chars(text)
    target_words = int(plan_data.get("target_words", 3000))
    if word_count < target_words * 0.45:
        warnings.append(f"正文长度偏短：当前约 {word_count} 字，明显低于目标 {target_words}。")
    if word_count > target_words * 1.6:
        warnings.append(f"正文长度偏长：当前约 {word_count} 字，明显高于目标 {target_words}。")

    if max_paragraph_length(text) > 260:
        warnings.append("存在较长段落，移动端阅读可能吃力。")

    ai_markers = find_ai_markers(text)
    if ai_markers:
        warnings.append(f"检测到可能的模板化表达：{', '.join(ai_markers[:5])}")

    if blockers:
        notes.append("当前草稿存在结构性问题，需先修成正文形态，再谈文风和节奏优化。")
    elif not warnings:
        notes.append("结构上无明显阻塞项，可以进入人审。")
    else:
        notes.append("建议先根据 Blocker / Warning 处理后再提交正式人审。")

    conclusion = "放行"
    if blockers:
        conclusion = "需修后复审"
    elif warnings:
        conclusion = "需修后复审"

    report_md = render_draft_review_md(
        chapter=args.chapter,
        title=plan_data["title"],
        version=draft_path.name,
        conclusion=conclusion,
        blockers=blockers,
        warnings=warnings,
        notes=notes,
    )
    report_path = root / "book" / "artifacts" / "reports" / f"chapter-{format_chapter(args.chapter)}-draft-review.md"
    review_data_path = chapter_dir / "draft-review.data.yaml"
    review_data = {
        "chapter": args.chapter,
        "title": plan_data["title"],
        "version": draft_path.name,
        "conclusion": conclusion,
        "blockers": blockers,
        "warnings": warnings,
        "notes": notes,
    }
    written, skipped = write_files(
        [(report_path, report_md), (review_data_path, dump_yaml(review_data))],
        force=args.force,
    )
    print_write_summary("review-draft", root, written, skipped)
    return 0 if written else 1


def run_sync_state(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    final_path = Path(args.final_file).resolve() if args.final_file else chapter_dir / "final.md"
    if not final_path.exists():
        print("sync-state 无法执行：缺少正式版本文件。可用 --final-file 指定。", file=sys.stderr)
        return 1

    review_data = load_yaml(chapter_dir / "draft-review.data.yaml")
    plan_data = load_plan_data(chapter_dir)
    if not plan_data:
        print("sync-state 无法执行：缺少 plan.data.yaml。", file=sys.stderr)
        return 1
    if not review_data:
        print("sync-state 无法执行：缺少 draft-review.data.yaml。", file=sys.stderr)
        return 1
    if review_data.get("blockers"):
        print("sync-state 无法执行：当前章仍存在未处理的 blocker。", file=sys.stderr)
        return 1
    final_gate = require_human_review_approval(chapter_dir, "final")
    if not final_gate[0]:
        print(f"sync-state 无法执行：{final_gate[1]}", file=sys.stderr)
        return 1

    text = final_path.read_text(encoding="utf-8")
    if PLACEHOLDER in text:
        print("sync-state 无法执行：final.md 仍包含“待补充”。", file=sys.stderr)
        return 1
    characters = load_yaml(root / "book" / "state" / "characters.yaml") or []
    factions = load_yaml(root / "book" / "state" / "factions.yaml") or []
    foreshadows = load_yaml(root / "book" / "state" / "foreshadows.yaml") or []
    power_state = load_yaml(root / "book" / "state" / "power_state.yaml") or {}
    chapter_index = load_yaml(root / "book" / "state" / "chapter_index.yaml") or []
    readiness = state_is_ready_for_planning(root)
    if not readiness[0]:
        print(f"sync-state 无法执行：{readiness[1]}", file=sys.stderr)
        return 1

    state_update_path = chapter_dir / "state-update.yaml"
    if not state_update_path.exists():
        scaffold = build_state_update_scaffold(args.chapter, plan_data, final_path.name, text)
        state_update_path.write_text(dump_yaml(scaffold), encoding="utf-8")
        print("sync-state 无法执行：缺少 state-update.yaml，已生成待填写脚手架。", file=sys.stderr)
        return 1

    state_update = load_yaml(state_update_path)
    validation_error = validate_state_update(state_update, final_text=text)
    if validation_error:
        print(f"sync-state 无法执行：{validation_error}", file=sys.stderr)
        return 1

    try:
        character_changes = apply_character_updates(characters, state_update.get("characters", []), args.chapter, text)
        faction_changes = apply_faction_updates(factions, state_update.get("factions", []), args.chapter, text)
        foreshadow_changes = apply_foreshadow_updates(foreshadows, state_update.get("foreshadows", []), args.chapter, text)
        power_changes = apply_power_updates(power_state, state_update.get("power_state", {}), text)
    except ValueError as exc:
        print(f"sync-state 无法执行：{exc}", file=sys.stderr)
        return 1

    chapter_index_payload = state_update.get("chapter_index", {}) if isinstance(state_update, dict) else {}
    summary = chapter_index_payload.get("summary") or summarize_text(text, 80)
    ending_hint = chapter_index_payload.get("ending_hook") or plan_data.get("ending_hint", "") or plan_data.get("ending_type", "待补充")
    chapter_record = {
        "chapter_no": args.chapter,
        "title": plan_data["title"],
        "volume": plan_data["volume"],
        "status": "final",
        "summary": summary,
        "must_payoff_ids": chapter_index_payload.get("must_payoff_ids") or plan_data.get("must_payoff_ids", []),
        "new_state_changes": chapter_index_payload.get("new_state_changes") or character_changes + faction_changes + foreshadow_changes + power_changes,
        "ending_hook": ending_hint,
    }
    upsert_chapter_index(chapter_index, chapter_record)

    write_yaml(root / "book" / "state" / "characters.yaml", characters)
    write_yaml(root / "book" / "state" / "factions.yaml", factions)
    write_yaml(root / "book" / "state" / "foreshadows.yaml", foreshadows)
    write_yaml(root / "book" / "state" / "power_state.yaml", power_state)
    write_yaml(root / "book" / "state" / "chapter_index.yaml", chapter_index)

    no_changes = []
    if not character_changes:
        no_changes.append("角色状态未写入结构性变化")
    if not faction_changes:
        no_changes.append("势力状态未写入结构性变化")
    if not foreshadow_changes:
        no_changes.append("伏笔状态未写入结构性变化")
    if not power_changes:
        no_changes.append("能力 / 资源状态未写入结构性变化")

    report_md = render_state_diff_md(
        chapter=args.chapter,
        title=plan_data["title"],
        final_name=final_path.name,
        character_changes=character_changes,
        faction_changes=faction_changes,
        foreshadow_changes=foreshadow_changes,
        power_changes=power_changes,
        no_changes=no_changes,
    )
    report_path = root / "book" / "artifacts" / "reports" / f"chapter-{format_chapter(args.chapter)}-state-diff.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"sync-state 已执行。目标目录: {root}")
    print(f"- 已更新 book/state/*.yaml")
    print(f"- 已写入 {report_path.relative_to(root)}")
    return 0


def run_render_artifacts(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    characters = load_yaml(root / "book" / "state" / "characters.yaml") or []
    factions = load_yaml(root / "book" / "state" / "factions.yaml") or []
    foreshadows = load_yaml(root / "book" / "state" / "foreshadows.yaml") or []
    power_state = load_yaml(root / "book" / "state" / "power_state.yaml") or {}
    chapter_index = load_yaml(root / "book" / "state" / "chapter_index.yaml") or []

    recaps_dir = root / "book" / "artifacts" / "recaps"
    recaps_dir.mkdir(parents=True, exist_ok=True)
    plot_path = recaps_dir / "plot-recap.md"
    state_path = recaps_dir / "state-recap.md"

    plot_md = render_plot_recap_md(chapter_index)
    state_md = render_state_recap_md(characters, factions, foreshadows, power_state)

    written, skipped = write_files([(plot_path, plot_md), (state_path, state_md)], force=args.force)
    print_write_summary("render-artifacts", root, written, skipped)
    return 0 if written else 1


def ensure_book_dirs(root: Path) -> None:
    ensure_dirs(
        [
            root / "book" / "canon",
            root / "book" / "canon" / "characters",
            root / "book" / "canon" / "volumes",
            root / "book" / "state",
            root / "book" / "drafts",
            root / "book" / "artifacts" / "reports",
            root / "book" / "artifacts" / "recaps",
        ]
    )


def ensure_dirs(paths: list[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def write_files(files: list[tuple[Path, str]], force: bool) -> tuple[list[Path], list[Path]]:
    written: list[Path] = []
    skipped: list[Path] = []
    for path, content in files:
        if write_file(path, content, force=force):
            written.append(path)
        else:
            skipped.append(path)
    return written, skipped


def write_file(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        existing = path.read_text(encoding="utf-8")
        if not can_overwrite_placeholder(existing):
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def can_overwrite_placeholder(existing: str) -> bool:
    normalized = existing.strip()
    if not normalized:
        return True
    placeholder_markers = [
        PLACEHOLDER,
        "初始仅主角",
        "[]",
        "# state",
        "初始化摘要",
        "这里开始写正文",
        "章节计划",
        "正文审稿报告",
        "状态差异报告",
        "剧情回顾",
        "状态总览",
    ]
    return any(marker in normalized for marker in placeholder_markers)


def load_yaml(path: Path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    return yaml.safe_load(text)


def dump_yaml(data) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def write_yaml(path: Path, data) -> None:
    path.write_text(dump_yaml(data), encoding="utf-8")


def get_chapter_dir(root: Path, chapter: int) -> Path:
    return root / "book" / "drafts" / f"chapter-{format_chapter(chapter)}"


def format_chapter(chapter: int) -> str:
    return f"{chapter:03d}"


def get_human_review_path(chapter_dir: Path, stage: str) -> Path:
    return chapter_dir / f"human-{stage}-review.yaml"


def extract_book_title(root: Path) -> str | None:
    premise_path = root / "book" / "canon" / "premise.md"
    if not premise_path.exists():
        return None
    text = premise_path.read_text(encoding="utf-8")
    match = re.search(r"《(.+?)》", text)
    return match.group(1) if match else None


def extract_genre(root: Path) -> str | None:
    premise_path = root / "book" / "canon" / "premise.md"
    if not premise_path.exists():
        return None
    text = premise_path.read_text(encoding="utf-8")
    match = re.search(r"面向\s+.+?\s+的\s+(.+?)，", text)
    return match.group(1) if match else None


def extract_platform(root: Path) -> str | None:
    premise_path = root / "book" / "canon" / "premise.md"
    if not premise_path.exists():
        return None
    text = premise_path.read_text(encoding="utf-8")
    match = re.search(r"面向\s+(.+?)\s+的", text)
    return match.group(1) if match else None


def extract_hook(root: Path) -> str | None:
    premise_path = root / "book" / "canon" / "premise.md"
    if not premise_path.exists():
        return None
    text = premise_path.read_text(encoding="utf-8")
    match = re.search(r"围绕“(.+?)”展开", text)
    return match.group(1) if match else None


def extract_protagonist_name(root: Path) -> str | None:
    path = root / "book" / "canon" / "characters" / "protagonist.md"
    if not path.exists():
        path = root / "book" / "state" / "characters.yaml"
        if path.exists():
            data = load_yaml(path) or []
            if data:
                return data[0].get("name")
        return None
    text = path.read_text(encoding="utf-8")
    match = re.search(r"- 姓名：(.+)", text)
    return match.group(1).strip() if match else None


def state_is_ready_for_planning(root: Path) -> tuple[bool, str]:
    premise = root / "book" / "canon" / "premise.md"
    setting = root / "book" / "canon" / "setting.md"
    if not premise.exists() or not setting.exists():
        return False, "canon 基础文件缺失。"

    issues = collect_init_readiness_issues(root)
    if issues:
        return False, f"初始化信息不足，至少先补齐这些关键项：{'；'.join(issues[:6])}"
    return True, ""


def require_human_review_approval(chapter_dir: Path, stage: str) -> tuple[bool, str]:
    review_data = load_yaml(get_human_review_path(chapter_dir, stage))
    if not review_data:
        stage_label = "章节计划" if stage == "plan" else "正文定稿"
        return False, f"缺少 {stage_label} 的人工审核记录，请先执行 record-review。"
    if review_data.get("decision") != "approved":
        stage_label = "章节计划" if stage == "plan" else "正文定稿"
        return False, f"{stage_label} 当前未被标记为 approved。"
    return True, ""


def collect_init_readiness_issues(root: Path) -> list[str]:
    issues: list[str] = []

    premise_path = root / "book" / "canon" / "premise.md"
    setting_path = root / "book" / "canon" / "setting.md"
    style_path = root / "book" / "canon" / "style_rules.md"
    protagonist_path = root / "book" / "canon" / "characters" / "protagonist.md"
    volume_path = root / "book" / "canon" / "volumes" / "volume-01-outline.md"
    characters_path = root / "book" / "state" / "characters.yaml"
    power_path = root / "book" / "state" / "power_state.yaml"

    issues.extend(check_markdown_bullets(premise_path, ["核心上头点", "主线问题"], "premise.md"))
    issues.extend(check_markdown_bullets(setting_path, ["时间背景", "空间背景", "社会环境", "约束条件"], "setting.md"))
    issues.extend(check_markdown_bullets(style_path, ["目标气质", "钩子类型偏好"], "style_rules.md"))
    issues.extend(check_markdown_bullets(protagonist_path, ["身份", "初始处境", "短期必须解决的问题"], "protagonist.md"))

    volume_text = volume_path.read_text(encoding="utf-8") if volume_path.exists() else ""
    if not volume_text:
        issues.append("volume-01-outline.md 缺失")
    else:
        issues.extend(check_section_bullets(volume_text, "### 阶段一", ["冲突", "结果"], "volume-01-outline.md"))

    characters = load_yaml(characters_path) or []
    if not isinstance(characters, list) or not characters:
        issues.append("characters.yaml 缺少主角条目")
    else:
        protagonist = characters[0]
        for key, label in [
            ("name", "characters.yaml 主角 name"),
            ("current_location", "characters.yaml 主角 current_location"),
            ("capability_summary", "characters.yaml 主角 capability_summary"),
        ]:
            if not is_actionable_context(protagonist.get(key)):
                issues.append(f"{label} 仍是占位值")
        open_threads = protagonist.get("open_threads") or []
        if not isinstance(open_threads, list) or not any(is_actionable_context(item) for item in open_threads):
            issues.append("characters.yaml 主角 open_threads 仍未填实")

    power_state = load_yaml(power_path) or {}
    if not isinstance(power_state, dict):
        issues.append("power_state.yaml 结构无效")
    else:
        protagonist_power = power_state.get("protagonist", {}) if isinstance(power_state.get("protagonist"), dict) else {}
        if not is_actionable_context(protagonist_power.get("baseline_power")):
            issues.append("power_state.yaml protagonist.baseline_power 仍是占位值")
        constraints = protagonist_power.get("current_constraints") or []
        if not isinstance(constraints, list) or not any(is_actionable_context(item) for item in constraints):
            issues.append("power_state.yaml protagonist.current_constraints 仍未填实")
        rules = power_state.get("systems_or_rules") or []
        if not isinstance(rules, list) or not any(is_actionable_context(item) for item in rules):
            issues.append("power_state.yaml systems_or_rules 仍未填实")

    return issues


def check_markdown_bullets(path: Path, labels: list[str], file_label: str) -> list[str]:
    if not path.exists():
        return [f"{file_label} 缺失"]
    text = path.read_text(encoding="utf-8")
    issues = []
    for label in labels:
        value = extract_markdown_bullet_value(text, label)
        if not is_actionable_context(value):
            issues.append(f"{file_label} 的“{label}”仍是占位值")
    return issues


def extract_markdown_bullet_value(text: str, label: str) -> str | None:
    match = re.search(rf"- {re.escape(label)}：(.+)", text)
    return match.group(1).strip() if match else None


def check_section_bullets(text: str, heading: str, labels: list[str], file_label: str) -> list[str]:
    section = extract_heading_section(text, heading)
    if not section:
        return [f"{file_label} 缺少 {heading}"]
    issues = []
    for label in labels:
        value = extract_markdown_bullet_value(section, label)
        if not is_actionable_context(value):
            issues.append(f"{file_label} 的 {heading} -> “{label}”仍是占位值")
    return issues


def extract_heading_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    current_level = None
    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if line.strip() == heading:
                in_section = True
                current_level = level
                collected.append(line)
                continue
            if in_section and current_level is not None and level <= current_level:
                break
        if in_section:
            collected.append(line)
    return "\n".join(collected).strip()


def load_brief_text(args: argparse.Namespace) -> str | None:
    if args.brief_file:
        return Path(args.brief_file).read_text(encoding="utf-8")
    return args.brief_text


def parse_brief_text(text: str) -> dict:
    parsed_yaml = parse_brief_yaml(text)
    if parsed_yaml is not None:
        return parsed_yaml

    result: dict[str, object] = {
        "must_nodes": [],
        "beat_suggestions": [],
        "risks": [],
    }
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current = line.replace("## ", "").strip()
            continue
        if line.startswith("- "):
            item = line[2:].strip()
            if current == "基础信息":
                key, _, value = item.partition("：")
                if key == "章节标题":
                    result["title"] = value.strip()
            elif current == "本章目标":
                result["goal"] = item.split("：", 1)[-1].strip()
            elif current == "必写节点":
                result["must_nodes"].append(item.split("：", 1)[-1].strip())
            elif current == "节拍建议":
                result["beat_suggestions"].append(item.split("：", 1)[-1].strip())
            elif current == "本章风险":
                result["risks"].append(item.split("：", 1)[-1].strip())
            elif current == "章末落点":
                result["ending"] = item.split("：", 1)[-1].strip()
    return result


def parse_brief_yaml(text: str) -> dict[str, object] | None:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return normalize_brief_mapping(data)


def normalize_brief_mapping(data: dict) -> dict[str, object]:
    result: dict[str, object] = {
        "must_nodes": normalize_text_list(data.get("must_nodes") or data.get("必写节点")),
        "beat_suggestions": normalize_text_list(data.get("beat_suggestions") or data.get("节拍建议")),
        "risks": normalize_text_list(data.get("risks") or data.get("本章风险")),
    }
    scalar_aliases = {
        "title": ["title", "章节标题"],
        "goal": ["goal", "本章目标"],
        "ending": ["ending", "章末落点"],
        "volume": ["volume", "所属卷"],
        "ending_type": ["ending_type", "结束类型", "章末类型"],
        "target_words": ["target_words", "字数", "目标字数"],
    }
    for target_key, aliases in scalar_aliases.items():
        for alias in aliases:
            value = data.get(alias)
            if value not in (None, ""):
                if target_key == "target_words":
                    parsed = coerce_positive_int(value)
                    if parsed is not None:
                        result[target_key] = parsed
                else:
                    result[target_key] = str(value).strip()
                break
    return result


def normalize_text_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value]
    else:
        text = str(value).strip()
        if not text:
            return []
        items = [part.strip("- ").strip() for part in re.split(r"[\r\n]+", text)]
    return [item for item in items if item]


def coerce_positive_int(value) -> int | None:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def is_meaningful_text(value) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and PLACEHOLDER not in text


def is_actionable_context(value) -> bool:
    if not is_meaningful_text(value):
        return False
    text = str(value).strip()
    blocked_fragments = [
        "当前没有必须推进的结构化伏笔",
        "角色状态待补充",
        "势力状态待补充",
        "能力/资源状态待补充",
    ]
    return not any(fragment in text for fragment in blocked_fragments)


def select_open_foreshadows(root: Path) -> list[str]:
    items = load_yaml(root / "book" / "state" / "foreshadows.yaml") or []
    selected = []
    for item in items:
        if item.get("current_status") in {"open", "advanced"} and item.get("id"):
            selected.append(item["id"])
        if len(selected) >= 2:
            break
    return selected


def build_state_constraints(root: Path) -> dict[str, str]:
    protagonist = extract_protagonist_name(root) or "主角"
    return {
        "人物约束": f"{protagonist} 的基础人设不得被当前章改写",
        "势力约束": "如无正文明确描写，不得自行改变势力关系",
        "资源约束": "关键资源变化必须能在正文中找到依据",
        "伏笔约束": "must_payoff_ids 中的项目至少要推进或明确延后",
    }


def extract_style_rules_summary(root: Path) -> list[str]:
    path = root / "book" / "canon" / "style_rules.md"
    if not path.exists():
        return ["风格规则待补充"]
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- "):
            value = line[2:].strip()
            if value and PLACEHOLDER not in value:
                lines.append(value)
    return lines[:6] or ["风格规则待补充"]


def load_previous_context(root: Path, chapter: int) -> str:
    if chapter <= 1:
        return "这是第 1 章，无上一章上下文。"
    previous_dir = get_chapter_dir(root, chapter - 1)
    final_path = previous_dir / "final.md"
    if final_path.exists():
        return summarize_text(final_path.read_text(encoding="utf-8"), 120)
    chapter_index = load_yaml(root / "book" / "state" / "chapter_index.yaml") or []
    for item in chapter_index:
        if item.get("chapter_no") == chapter - 1:
            return item.get("summary", "待补充")
    return "上一章上下文待补充。"


def infer_chapter_mode(goal: str, beats: list[dict], ending_type: str) -> str:
    text = " ".join([goal, ending_type] + [str(beat.get("name", "")) for beat in beats])
    if any(keyword in text for keyword in ["战", "杀", "逃", "追", "围攻", "暴击", "出手"]):
        return "强冲突推进章"
    if any(keyword in text for keyword in ["揭秘", "真相", "发现", "情报", "规则", "线索"]):
        return "信息揭示章"
    if any(keyword in text for keyword in ["关系", "和解", "决裂", "告白", "背叛"]):
        return "关系变化章"
    return "常规推进章"


def collect_key_characters(root: Path, protagonist_name: str, limit: int = 5) -> list[str]:
    items = load_yaml(root / "book" / "state" / "characters.yaml") or []
    if not isinstance(items, list):
        return [f"{protagonist_name}：角色状态待补充"]

    def sort_key(item: dict) -> tuple[int, int]:
        is_protagonist = 0 if item.get("name") == protagonist_name or item.get("id") == "protagonist" else 1
        latest_chapter = int(item.get("latest_chapter", 0) or 0)
        return (is_protagonist, -latest_chapter)

    summaries = []
    for item in sorted(items, key=sort_key)[:limit]:
        name = item.get("name") or item.get("id") or PLACEHOLDER
        status = item.get("status", PLACEHOLDER)
        location = item.get("current_location", PLACEHOLDER)
        relation = item.get("relationship_to_protagonist", PLACEHOLDER)
        capability = item.get("capability_summary", PLACEHOLDER)
        open_threads = item.get("open_threads") or []
        parts = []
        if is_meaningful_text(status):
            parts.append(f"状态={status}")
        if is_meaningful_text(location):
            parts.append(f"位置={location}")
        if is_meaningful_text(relation):
            parts.append(f"与主角关系={relation}")
        if is_meaningful_text(capability):
            parts.append(f"作用/能力={capability}")
        if isinstance(open_threads, list):
            meaningful_threads = [thread for thread in open_threads if is_meaningful_text(thread)]
            if meaningful_threads:
                parts.append(f"当前悬而未决={meaningful_threads[0]}")
        summary = f"{name}：" + ("；".join(parts) if parts else "角色状态待补充")
        summaries.append(summary)
    return summaries or [f"{protagonist_name}：角色状态待补充"]


def collect_key_factions(root: Path, limit: int = 4) -> list[str]:
    items = load_yaml(root / "book" / "state" / "factions.yaml") or []
    if not isinstance(items, list) or not items:
        return ["势力状态待补充"]
    summaries = []
    for item in items[:limit]:
        name = item.get("name") or item.get("id") or PLACEHOLDER
        relation = item.get("relationship_to_protagonist", PLACEHOLDER)
        territory = item.get("territory", PLACEHOLDER)
        resources = [resource for resource in normalize_text_list(item.get("resources")) if is_meaningful_text(resource)][:2]
        parts = []
        if is_meaningful_text(relation):
            parts.append(f"与主角关系={relation}")
        if is_meaningful_text(territory):
            parts.append(f"据点={territory}")
        if resources:
            parts.append(f"关键资源={', '.join(resources)}")
        summaries.append(f"{name}：" + ("；".join(parts) if parts else "势力状态待补充"))
    return summaries


def collect_key_foreshadows(root: Path, must_payoff_ids: list[str], limit: int = 4) -> list[str]:
    items = load_yaml(root / "book" / "state" / "foreshadows.yaml") or []
    if not isinstance(items, list):
        items = []

    selected = []
    must_ids = set(must_payoff_ids or [])
    for item in items:
        if item.get("id") in must_ids:
            selected.append(item)
    if len(selected) < limit:
        for item in items:
            if item in selected:
                continue
            if item.get("current_status") in {"open", "advanced"}:
                selected.append(item)
            if len(selected) >= limit:
                break

    summaries = []
    for item in selected[:limit]:
        identifier = item.get("id", PLACEHOLDER)
        desc = item.get("description", PLACEHOLDER)
        status = item.get("current_status", PLACEHOLDER)
        payoff = item.get("expected_payoff_window", PLACEHOLDER)
        summaries.append(f"{identifier}：{desc}；当前状态={status}；预期回收窗口={payoff}")
    return summaries or ["当前没有必须推进的结构化伏笔，若正文新增伏笔，后续必须补回 state。"]


def collect_power_snapshot(root: Path) -> list[str]:
    data = load_yaml(root / "book" / "state" / "power_state.yaml") or {}
    if not isinstance(data, dict):
        return ["能力/资源状态待补充"]

    protagonist = data.get("protagonist", {}) if isinstance(data.get("protagonist"), dict) else {}
    lines = []
    baseline = protagonist.get("baseline_power")
    if is_meaningful_text(baseline):
        lines.append(f"主角基础战力：{baseline}")
    for item in [value for value in normalize_text_list(protagonist.get("current_constraints")) if is_meaningful_text(value)][:2]:
        lines.append(f"主角当前限制：{item}")
    for label in ["key_items", "companions", "base_or_assets", "rare_resources"]:
        values = [value for value in normalize_text_list(data.get(label)) if is_meaningful_text(value)][:2]
        for value in values:
            lines.append(f"{label}：{value}")
    return lines[:6] or ["能力/资源状态待补充"]


def collect_taboos(root: Path, risks: list[str], limit: int = 8) -> list[str]:
    keywords = ("禁", "不要", "不能", "红线", "高风险")
    lines = list(risks or [])
    for path in [
        root / "book" / "canon" / "premise.md",
        root / "book" / "canon" / "setting.md",
        root / "book" / "canon" / "style_rules.md",
        root / "book" / "canon" / "characters" / "protagonist.md",
    ]:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line.startswith("- "):
                continue
            value = line[2:].strip()
            if PLACEHOLDER in value:
                continue
            if any(keyword in value for keyword in keywords):
                lines.append(value)
    unique = []
    for item in lines:
        if item and item not in unique:
            unique.append(item)
    default_items = [
        "不得改写已确认 canon / state 中的长期事实",
        "不得为了制造爽点而跳过必要铺垫",
        "不得把下一章主冲突提前透支完",
    ]
    for item in default_items:
        if item not in unique:
            unique.append(item)
    return unique[:limit]


def build_draft_continuity_hints(prompt_data: dict) -> list[str]:
    hints = []
    for item in prompt_data.get("key_characters", [])[:2]:
        if is_actionable_context(item):
            hints.append(item)
    for item in prompt_data.get("state_constraints", {}).values():
        if is_actionable_context(item):
            hints.append(str(item))
        if len(hints) >= 4:
            break
    return hints


def render_offline_draft_markdown(
    *,
    chapter: int,
    title: str,
    protagonist_name: str,
    goal: str,
    previous_context: str,
    beats: list[dict],
    must_nodes: list[str],
    style_rules: list[str],
    key_foreshadows: list[str],
    power_snapshot: list[str],
    ending_type: str,
    ending_hint: str,
) -> str:
    sections = [f"# 第{chapter}章：{title}", ""]
    opening = build_opening_paragraph(chapter=chapter, protagonist_name=protagonist_name, goal=goal, previous_context=previous_context)
    sections.extend(opening)

    for index, beat in enumerate(beats, start=1):
        node_hint = must_nodes[index - 1] if index - 1 < len(must_nodes) else ""
        foreshadow_hint = key_foreshadows[min(index - 1, len(key_foreshadows) - 1)] if key_foreshadows else ""
        power_hint = power_snapshot[min(index - 1, len(power_snapshot) - 1)] if power_snapshot else ""
        beat_text = render_offline_beat_scene(
            protagonist_name=protagonist_name,
            beat=beat,
            node_hint=node_hint,
            foreshadow_hint=foreshadow_hint,
            power_hint=power_hint,
            style_rules=style_rules,
            is_first=index == 1,
            is_last=index == len(beats),
        )
        sections.extend(beat_text)

    sections.append(build_ending_echo(protagonist_name=protagonist_name, ending_type=ending_type, ending_hint=ending_hint))
    return "\n".join(sections).strip() + "\n"


def build_opening_paragraph(*, chapter: int, protagonist_name: str, goal: str, previous_context: str) -> list[str]:
    if chapter > 1 and is_actionable_context(previous_context):
        return [
            previous_context.rstrip("。") + "。",
            "",
            f"{protagonist_name}还没来得及把上一章的余波理顺，新的麻烦已经顶到了眼前。",
            "",
        ]
    return [
        f"{protagonist_name}今晚最怕的不是差评，也不是淋雨。",
        "",
        f"他真正怕的是再晚一点，银行卡里那点可怜的余额就撑不住房贷，而他连继续硬扛的资格都没有。目标只有一个：{goal.rstrip('。')}。",
        "",
    ]


def render_offline_beat_scene(
    *,
    protagonist_name: str,
    beat: dict,
    node_hint: str,
    foreshadow_hint: str,
    power_hint: str,
    style_rules: list[str],
    is_first: bool,
    is_last: bool,
) -> list[str]:
    seed = strip_prompt_scaffold(beat.get("scene_seed") or beat.get("key_action") or "")
    landing = strip_prompt_scaffold(beat.get("landing") or "")
    beat_name = strip_prompt_scaffold(beat.get("name") or "本节")
    scene_hint = " ".join(
        item
        for item in [seed, beat_name, strip_prompt_leakage(node_hint), strip_prompt_leakage(foreshadow_hint)]
        if is_actionable_context(item)
    )
    scene_blocks = build_scene_blocks_from_keywords(
        protagonist_name=protagonist_name,
        scene_hint=scene_hint,
        landing=landing,
        is_first=is_first,
        is_last=is_last,
    )
    if scene_blocks:
        paragraphs: list[str] = []
        for block in scene_blocks:
            paragraphs.append(block)
            paragraphs.append("")
        return paragraphs

    fragments = extract_story_fragments([node_hint, foreshadow_hint, power_hint])
    lead = f"{beat_name}刚露头，{protagonist_name}就知道今晚不会平顺。"
    fallback = [
        lead,
        "",
        f"{protagonist_name}没有空站着分析，只能先动起来，把“{seed or beat_name}”变成眼前的实际麻烦。{fragments[0] if fragments else ''}".strip(),
        "",
        f"等他把这一步扛过去，真正等着他的，还是“{landing or '更难回头'}”背后那层更深的代价。",
        "",
    ]
    return fallback


def build_ending_echo(*, protagonist_name: str, ending_type: str, ending_hint: str) -> str:
    if ending_type == "钩子推进":
        return f"{protagonist_name}抬头的时候，已经有人先一步盯上了他。{ending_hint.rstrip('。')}。"
    return f"{protagonist_name}知道，这一章落下去以后，下一步只会更难。{ending_hint.rstrip('。')}。"


def strip_prompt_scaffold(text: str) -> str:
    if not is_actionable_context(text):
        return ""
    cleaned = str(text)
    for marker in ["本节功能", "必须发生", "冲突焦点", "结果落点", "不要写成", "场景种子"]:
        cleaned = cleaned.replace(marker, "")
    cleaned = cleaned.replace("：", " ").replace("=", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" 。；;，,")
    return cleaned


def extract_story_fragments(items: list[str]) -> list[str]:
    fragments: list[str] = []
    for item in items:
        if not is_actionable_context(item):
            continue
        cleaned = strip_prompt_leakage(str(item))
        if cleaned and cleaned not in fragments:
            fragments.append(cleaned)
    return fragments[:3]


def strip_prompt_leakage(text: str) -> str:
    cleaned = str(text)
    replacements = [
        "当前没有必须推进的结构化伏笔，若正文新增伏笔，后续必须补回 state。",
        "人物约束：",
        "势力约束：",
        "资源约束：",
        "伏笔约束：",
        "目标气质：",
        "节奏偏好：",
        "对话风格：",
        "段落长度：",
        "钩子类型偏好：",
        "主角基础战力：",
        "主角当前限制：",
        "key_items：",
        "base_or_assets：",
    ]
    for item in replacements:
        cleaned = cleaned.replace(item, "")
    cleaned = cleaned.replace("状态=", "").replace("位置=", "").replace("关系=", "").replace("作用/能力=", "")
    cleaned = cleaned.replace("当前悬而未决=", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" ；;，,。")


def clean_prompt_leakage(text: str) -> str:
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    forbidden = (
        "这一节必须承担",
        "冲突焦点",
        "不要写成",
        "本章核心目标",
        "目标气质：",
        "key_items：",
        "主角当前限制：",
        "状态=",
        "位置=",
        "作用/能力=",
    )
    for line in lines:
        if any(marker in line for marker in forbidden):
            continue
        cleaned = line.replace("眼下最直接的掣肘有三个：", "")
        cleaned = cleaned.replace("章末必须落在“", "章末落在“")
        cleaned = cleaned.strip()
        if cleaned:
            cleaned_lines.append(cleaned)
        else:
            cleaned_lines.append("")
    return "\n".join(cleaned_lines)


def normalize_dialogue_spacing(text: str) -> str:
    normalized = re.sub(r"([。！？])([^\n”])", r"\1\n\2", text)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def detect_prompt_leakage_markers(text: str) -> list[str]:
    markers = [
        "本章核心目标",
        "这一节必须承担",
        "冲突焦点",
        "不要写成",
        "key_items：",
        "主角当前限制：",
        "目标气质：",
        "状态=",
        "位置=",
        "关系=",
        "作用/能力=",
    ]
    return [marker for marker in markers if marker in text]


def looks_like_narrative_prose(text: str) -> bool:
    body = re.sub(r"^#.+$", "", text, flags=re.MULTILINE).strip()
    if not body:
        return False
    paragraphs = [item.strip() for item in body.split("\n\n") if item.strip()]
    if len(paragraphs) < 4:
        return False
    action_tokens = ["说", "看", "冲", "跑", "抬", "回", "咬牙", "手", "脚", "门", "车"]
    action_hits = sum(1 for token in action_tokens if token in body)
    return action_hits >= 5


def build_scene_blocks_from_keywords(
    *,
    protagonist_name: str,
    scene_hint: str,
    landing: str,
    is_first: bool,
    is_last: bool,
) -> list[str]:
    hint = scene_hint
    if any(keyword in hint for keyword in ["急送", "接单", "高价"]):
        return [
            f"就在{protagonist_name}准备接下一单普通夜宵的时候，骑手软件忽然弹出一条急送单。价格高得离谱，配送时限却短得像是故意不让人活。",
            f"更怪的是，这单没有正常商家备注，取货地址卡在一条老旧巷子里，送达点却在城西一栋快废弃的写字楼。正常骑手看到这种单，多半第一反应就是绕着走。",
            f"{protagonist_name}也想关掉界面，可他盯着那串配送费看了三秒，脑子里先跳出来的不是风险，而是这个月还差的房贷尾巴。手指只犹豫了一下，单子就被他抢了下来。局面也从这一秒开始，彻底朝着“{landing or '更难回头'}”的方向滑过去。",
        ]
    if any(keyword in hint for keyword in ["车祸", "觉醒", "超时"]):
        return [
            f"赶往送达点的路上，红灯刚跳黄，侧面一辆面包车就像看不见人一样猛拐过来。{protagonist_name}只来得及骂半句，整个人连车带包一起飞了出去。",
            f"柏油路蹭得他手臂火辣辣地疼，脑子也嗡的一下发白。可更要命的是，屏幕上的倒计时还在往下跳，包裹还滚在不远处，像是在提醒他这单一旦超时，今晚就白折腾了。",
            f"就在他咬牙爬起来那一瞬，胸口像是被什么东西猛地顶开。呼吸忽然顺了，腿上的酸胀像被一把扯断，连雨点落下来的速度都像慢了一拍。{protagonist_name}没空理解那是什么，他只知道自己必须先把包捡回来，然后继续往前冲。",
        ]
    if any(keyword in hint for keyword in ["送到", "收益", "新能力"]):
        return [
            f"包裹重新回到手里后，{protagonist_name}第一次知道什么叫脚底发轻。楼梯一层层往上扑，他却像把平时那些喘不过气的拐角全都踩平了。",
            f"平时要停两次的长楼道，这回他一口气冲到顶。门开的时候，收货人先是盯了他一眼，像没想到这种时间还真有人能把东西送到，随后才伸手把包裹接过去。",
            f"到账提示响起来的那一刻，{protagonist_name}心里先是一松，紧接着又猛地一紧。钱是真的，速度也是真的，可越是这样，他越能感觉到自己已经踩进了一个不该碰的局里。",
        ]
    if any(keyword in hint for keyword in ["异常", "盯上", "麻烦", "掉包"]):
        hook = f"{protagonist_name}站在空荡荡的走廊口，后背的冷汗一下就冒出来了。钱是到账了，可真正的麻烦这才露头。有人已经盯上他，而且对方显然不打算给他解释的机会。"
        if is_last:
            hook += f"事情也顺着“{landing or '新的危险'}”追到了他脚边。"
        return [
            f"电梯门刚合上，{protagonist_name}就察觉到不对。刚才那人接包裹时动作太快，像是在确认什么，又像是在掩饰什么，连一句正常的“辛苦了”都没说。",
            f"更诡异的是，他低头再看订单页面，那条急送记录竟然开始异常闪烁，像是有人在后台强行改动数据。下一秒，一条陌生短信跳了出来，内容只有一句话：东西没在你手里，最好拿下一单证明。",
            hook,
        ]
    if any(keyword in hint for keyword in ["房贷", "跑单", "现实压力", "外卖"]):
        return [
            f"夜里十一点多，{protagonist_name}蹲在商场后门啃冷掉的手抓饼，手机里那条房贷扣款提醒像根鱼刺，一直卡在喉咙口。",
            f"他白天刚被站长阴阳怪气，说这个月再掉单就别想拿满勤。可他比谁都清楚，自己现在最丢不起的不是面子，是那套还在还贷的房子。一旦现金流断了，父母留下来的最后一点东西都得跟着一起断。",
            f"所以哪怕腿已经酸得发涨，雨也开始往脖子里灌，他还是得把电动车重新扶正。对别人来说，送外卖只是份活；对他来说，这是眼下唯一还能把日子往明天拖一拖的办法。",
        ]
    return []


def build_state_update_scaffold(chapter: int, plan_data: dict, final_name: str, final_text: str) -> dict:
    return {
        "meta": {
            "chapter": chapter,
            "title": plan_data.get("title", f"第{chapter}章"),
            "source_final": final_name,
            "instructions": [
                "只填写正文里明确出现、且会影响后续写作判断的长期事实",
                "每个更新项都必须填写 evidence，且 evidence 片段应直接来自 final.md",
                "没有发生变化的领域保持空列表，不要凭推测补写",
            ],
        },
        "characters": [],
        "factions": [],
        "foreshadows": [],
        "power_state": {
            "protagonist": {
                "baseline_power": "",
                "current_constraints_add": [],
            },
            "systems_or_rules_add": [],
            "key_items_add": [],
            "companions_add": [],
            "base_or_assets_add": [],
            "rare_resources_add": [],
        },
        "chapter_index": {
            "summary": summarize_text(final_text, 80),
            "ending_hook": plan_data.get("ending_hint", ""),
            "must_payoff_ids": plan_data.get("must_payoff_ids", []),
            "new_state_changes": [],
        },
    }


def validate_state_update(state_update, *, final_text: str) -> str | None:
    if not isinstance(state_update, dict):
        return "state-update.yaml 结构无效。"
    for key in ["characters", "factions", "foreshadows"]:
        value = state_update.get(key, [])
        if not isinstance(value, list):
            return f"state-update.yaml 的 {key} 必须是列表。"
        for item in value:
            if not isinstance(item, dict):
                return f"state-update.yaml 的 {key} 中存在非法条目。"
            evidence = item.get("evidence")
            if not is_actionable_context(evidence):
                return f"{key} 中每个条目都必须填写 evidence。"
            if not evidence_matches_final(str(evidence), final_text):
                return f"{key} 中存在 evidence 无法在 final.md 中找到的条目。"

    power_state = state_update.get("power_state", {})
    if power_state and not isinstance(power_state, dict):
        return "state-update.yaml 的 power_state 必须是对象。"

    chapter_index = state_update.get("chapter_index", {})
    if chapter_index and not isinstance(chapter_index, dict):
        return "state-update.yaml 的 chapter_index 必须是对象。"
    summary = chapter_index.get("summary")
    if summary is not None and not is_actionable_context(summary):
        return "state-update.yaml 的 chapter_index.summary 不能为空或占位。"
    ending_hook = chapter_index.get("ending_hook")
    if ending_hook is not None and not is_actionable_context(ending_hook):
        return "state-update.yaml 的 chapter_index.ending_hook 不能为空或占位。"
    return None


def evidence_matches_final(evidence: str, final_text: str) -> bool:
    fragment = normalize_search_text(evidence)
    target = normalize_search_text(final_text)
    if len(fragment) < 4:
        return False
    return fragment[: min(len(fragment), 12)] in target


def normalize_search_text(text: str) -> str:
    return re.sub(r"[：:，。、“”\"'（）()\-\s]", "", text)


def apply_character_updates(characters: list[dict], updates: list[dict], chapter: int, final_text: str) -> list[str]:
    changes: list[str] = []
    for update in updates:
        identifier = update.get("id")
        name = update.get("name")
        item = find_record(characters, identifier=identifier, name=name)
        if item is None:
            if not identifier or not name:
                raise ValueError("characters 更新缺少 id / name，无法新增。")
            item = {
                "id": identifier,
                "name": name,
                "faction": "待补充",
                "status": "alive",
                "current_location": "待补充",
                "relationship_to_protagonist": "待补充",
                "capability_summary": "待补充",
                "latest_chapter": chapter,
                "open_threads": [],
            }
            characters.append(item)
            changes.append(f"新增角色 {name}")
        touched = False
        for key in ["faction", "status", "current_location", "relationship_to_protagonist", "capability_summary"]:
            if is_actionable_context(update.get(key)):
                item[key] = update[key]
                touched = True
        if update.get("latest_chapter") is not None:
            item["latest_chapter"] = int(update["latest_chapter"])
            touched = True
        else:
            item["latest_chapter"] = chapter
        extra_threads = [value for value in normalize_text_list(update.get("open_threads_add")) if is_actionable_context(value)]
        if extra_threads:
            item.setdefault("open_threads", [])
            for thread in extra_threads:
                if thread not in item["open_threads"]:
                    item["open_threads"].append(thread)
                    touched = True
        if touched:
            label = item.get("name", identifier or "角色")
            changes.append(f"{label} 状态已按本章正式版回写")
    return deduplicate_preserve_order(changes)


def apply_faction_updates(factions: list[dict], updates: list[dict], chapter: int, final_text: str) -> list[str]:
    changes: list[str] = []
    for update in updates:
        identifier = update.get("id")
        name = update.get("name")
        item = find_record(factions, identifier=identifier, name=name)
        if item is None:
            if not identifier or not name:
                raise ValueError("factions 更新缺少 id / name，无法新增。")
            item = {
                "id": identifier,
                "name": name,
                "leader": update.get("leader", "待补充"),
                "members_summary": update.get("members_summary", "待补充"),
                "territory": update.get("territory", "待补充"),
                "resources": [],
                "relationship_to_protagonist": update.get("relationship_to_protagonist", "待补充"),
                "latest_change_chapter": chapter,
            }
            factions.append(item)
            changes.append(f"新增势力 {name}")
        touched = False
        for key in ["leader", "members_summary", "territory", "relationship_to_protagonist"]:
            if is_actionable_context(update.get(key)):
                item[key] = update[key]
                touched = True
        resources_add = [value for value in normalize_text_list(update.get("resources_add")) if is_actionable_context(value)]
        if resources_add:
            item.setdefault("resources", [])
            for resource in resources_add:
                if resource not in item["resources"]:
                    item["resources"].append(resource)
                    touched = True
        if touched:
            item["latest_change_chapter"] = chapter
            changes.append(f"{item.get('name', identifier or '势力')} 状态已按本章正式版回写")
    return deduplicate_preserve_order(changes)


def apply_foreshadow_updates(foreshadows: list[dict], updates: list[dict], chapter: int, final_text: str) -> list[str]:
    changes: list[str] = []
    for update in updates:
        identifier = update.get("id")
        action = update.get("action")
        if not identifier or action not in {"add", "advance", "resolve", "close"}:
            raise ValueError("foreshadows 更新必须包含 id 和合法 action。")
        item = find_record(foreshadows, identifier=identifier, name=None)
        if item is None and action != "add":
            raise ValueError(f"伏笔 {identifier} 不存在，不能执行 {action}。")
        if item is None:
            item = {
                "id": identifier,
                "description": update.get("description", "待补充"),
                "introduced_in": chapter,
                "current_status": update.get("current_status", "open"),
                "related_characters": normalize_text_list(update.get("related_characters")),
                "expected_payoff_window": update.get("expected_payoff_window", "待补充"),
                "last_progress_chapter": chapter,
            }
            foreshadows.append(item)
            changes.append(f"新增伏笔 {identifier}")
        else:
            status_map = {
                "advance": "advanced",
                "resolve": "resolved",
                "close": "closed",
                "add": update.get("current_status", "open"),
            }
            item["current_status"] = status_map[action]
            item["last_progress_chapter"] = chapter
            if is_actionable_context(update.get("description")):
                item["description"] = update["description"]
            related_characters = [value for value in normalize_text_list(update.get("related_characters")) if is_actionable_context(value)]
            if related_characters:
                item["related_characters"] = related_characters
            if is_actionable_context(update.get("expected_payoff_window")):
                item["expected_payoff_window"] = update["expected_payoff_window"]
            changes.append(f"伏笔 {identifier} 已标记为 {item['current_status']}")
    return deduplicate_preserve_order(changes)


def apply_power_updates(power_state: dict, updates: dict, final_text: str) -> list[str]:
    if not updates:
        return []
    if not isinstance(power_state, dict):
        raise ValueError("power_state 当前结构无效。")
    if not isinstance(updates, dict):
        raise ValueError("state-update.yaml 的 power_state 结构无效。")
    changes: list[str] = []

    protagonist = power_state.setdefault("protagonist", {})
    protagonist_updates = updates.get("protagonist", {})
    if protagonist_updates and not isinstance(protagonist_updates, dict):
        raise ValueError("power_state.protagonist 更新结构无效。")
    baseline_power = protagonist_updates.get("baseline_power") if isinstance(protagonist_updates, dict) else None
    if is_actionable_context(baseline_power):
        protagonist["baseline_power"] = baseline_power
        changes.append("主角基础战力已更新")
    constraints_add = [value for value in normalize_text_list(protagonist_updates.get("current_constraints_add")) if is_actionable_context(value)] if isinstance(protagonist_updates, dict) else []
    if constraints_add:
        protagonist.setdefault("current_constraints", [])
        for value in constraints_add:
            if value not in protagonist["current_constraints"]:
                protagonist["current_constraints"].append(value)
                changes.append("主角限制条件已更新")

    for key, label in [
        ("systems_or_rules_add", "系统 / 规则"),
        ("key_items_add", "关键物品"),
        ("companions_add", "同伴战力"),
        ("base_or_assets_add", "基地 / 资产"),
        ("rare_resources_add", "稀有资源"),
    ]:
        values = [value for value in normalize_text_list(updates.get(key)) if is_actionable_context(value)]
        if not values:
            continue
        target_key = key.replace("_add", "")
        power_state.setdefault(target_key, [])
        for value in values:
            if value not in power_state[target_key]:
                power_state[target_key].append(value)
                changes.append(f"{label} 已更新")
    return deduplicate_preserve_order(changes)


def find_record(items: list[dict], *, identifier, name):
    for item in items:
        if identifier and item.get("id") == identifier:
            return item
        if name and item.get("name") == name:
            return item
    return None


def deduplicate_preserve_order(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def build_beats(
    *,
    protagonist_name: str,
    chapter_title: str,
    chapter_goal: str,
    target_words: int,
    beat_suggestions: list[str],
    ending_type: str,
) -> list[dict]:
    if beat_suggestions:
        raw_beats = beat_suggestions[:5]
    else:
        raw_beats = [
            "开场推进",
            "核心冲突",
            "局面反转或深化",
            "章末收束",
        ]
    budgets = allocate_budgets(target_words, len(raw_beats))
    beats = []
    for index, name in enumerate(raw_beats):
        label = compact_label(name, fallback=f"节拍{index + 1}")
        if index == 0:
            function = "建立本章起点并抛出必须立刻处理的麻烦"
            action = name if beat_suggestions else f"{protagonist_name}必须在开场就卷入“{chapter_goal}”"
            landing = "让主角无法退回原状态，读者明确知道本章主问题"
            scene_seed = name if beat_suggestions else f"{protagonist_name}被迫面对本章的第一道门槛"
            conflict_focus = f"{protagonist_name}必须在信息不完整时做出第一次选择"
            taboo = "不要把开场写成纯设定说明或纯气氛铺垫。"
        elif index == len(raw_beats) - 1:
            function = "完成本章收束并形成下一步承接"
            action = name if beat_suggestions else f"让{chapter_title}的主要矛盾完成当前阶段收束"
            landing = f"形成“{ending_type}”的明确结尾"
            scene_seed = name if beat_suggestions else f"{protagonist_name}拿到阶段性结果，同时暴露更大的后果"
            conflict_focus = "本章成果、代价和下一步威胁必须同时落地"
            taboo = "不要把章末钩子解释透，不要提前写穿下一章。"
        else:
            function = "推进核心矛盾，并让局势比上一节更难处理"
            action = name if beat_suggestions else f"{protagonist_name}需要围绕“{chapter_goal}”做出实质动作"
            landing = "把局势推向更贵、更险或更难回头的新阶段"
            scene_seed = name if beat_suggestions else f"{protagonist_name}必须把动作真正落到场面里"
            conflict_focus = f"{protagonist_name}需要付出代价，换来推进本章目标的资格"
            taboo = "不要只让角色嘴上判断局势，要让推进和代价同时发生。"
        beats.append(
            {
                "name": label,
                "function": function,
                "budget": budgets[index],
                "key_action": action,
                "landing": landing,
                "scene_seed": scene_seed,
                "conflict_focus": conflict_focus,
                "taboo": taboo,
            }
        )
    return beats


def allocate_budgets(target_words: int, beat_count: int) -> list[int]:
    if beat_count <= 1:
        return [target_words]
    if beat_count == 2:
        ratios = [0.45, 0.55]
    elif beat_count == 3:
        ratios = [0.25, 0.45, 0.30]
    elif beat_count == 5:
        ratios = [0.16, 0.22, 0.24, 0.22, 0.16]
    else:
        ratios = [0.2, 0.3, 0.3, 0.2]
    budgets = [int(target_words * ratio) for ratio in ratios[:beat_count]]
    diff = target_words - sum(budgets)
    budgets[-1] += diff
    return budgets


def compact_label(text: str, fallback: str) -> str:
    cleaned = re.split(r"[，。；：,.!?？!]", text.strip())[0]
    cleaned = cleaned[:16].strip()
    return cleaned or fallback


def render_plan_markdown(plan: dict) -> str:
    lines = [
        "# 章节计划",
        "",
        "## 一、基础信息",
        "",
        f"- 章节号：{plan['chapter']}",
        f"- 章节标题：{plan['title']}",
        f"- 所属卷：{plan['volume']}",
        "",
        "## 二、本章目标",
        "",
        f"- 本章最核心要推进的内容：{plan['goal']}",
        "",
        "## 三、字数预算",
        "",
        f"- 目标总字数：{plan['target_words']}",
        "- 允许浮动范围：±20%",
        "",
        "## 四、节拍拆分",
        "",
    ]
    for idx, beat in enumerate(plan["beats"], start=1):
        lines.extend(
            [
                f"### 节拍{idx}：{beat['name']}",
                "",
                f"- 功能：{beat['function']}",
                f"- 预算：约 {beat['budget']} 字",
                f"- 关键动作：{beat['key_action']}",
                f"- 落点：{beat['landing']}",
                "",
            ]
        )
    lines.extend(["## 五、必写节点", ""])
    for idx, node in enumerate(plan["must_nodes"], start=1):
        lines.append(f"- 节点 {idx}：{node}")
    lines.extend(["", "## 六、关键 state 约束", ""])
    for key, value in plan["state_constraints"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 七、风险与禁忌", ""])
    for idx, risk in enumerate(plan["risks"], start=1):
        lines.append(f"- 风险 {idx}：{risk}")
    lines.extend(
        [
            "",
            "## 八、章末落点",
            "",
            f"- 本章结束类型：{plan['ending_type']}",
            f"- 下一章承接方向：{plan['ending_hint']}",
        ]
    )
    return "\n".join(lines)


def render_prompt_markdown(
    *,
    book_title: str,
    chapter: int,
    title: str,
    volume: str,
    genre: str,
    platform: str,
    hook: str,
    chapter_mode: str,
    protagonist_name: str,
    goal: str,
    target_words: int,
    beats: list[dict],
    must_nodes: list[str],
    style_rules: list[str],
    state_constraints: dict[str, str],
    ending_type: str,
    ending_hint: str,
    previous_context: str,
    key_characters: list[str],
    key_factions: list[str],
    key_foreshadows: list[str],
    power_snapshot: list[str],
    taboos: list[str],
) -> str:
    lines = [
        "# 正文骨架",
        "",
        "## 一、写作任务",
        "",
        f"- 你现在要写《{book_title}》的第 {chapter} 章正文",
        f"- 作品定位：{genre} / {platform}",
        f"- 核心卖点：{hook}",
        f"- 本章类型：{chapter_mode}",
        f"- 主视角要求：核心视角围绕 {protagonist_name} 推进",
        "- 直接输出正文，不输出分析、计划说明或解释性备注",
        "",
        "## 二、章节基础信息",
        "",
        f"- 章节号：{chapter}",
        f"- 章节标题：{title}",
        f"- 所属卷：{volume}",
        "",
        "## 三、前情提要",
        "",
        f"- {previous_context}",
        "",
        "## 四、本章硬目标",
        "",
        f"- 本章核心目标：{goal}",
        f"- 目标字数：约 {target_words} 字",
        f"- 章末收束类型：{ending_type}",
        f"- 下一章承接方向：{ending_hint}",
        "",
        "## 五、必须调用的连续性信息",
        "",
        "### 关键角色",
        "",
    ]
    for item in key_characters:
        lines.append(f"- {item}")
    lines.extend(["", "### 关键势力", ""])
    for item in key_factions:
        lines.append(f"- {item}")
    lines.extend(["", "### 关键伏笔", ""])
    for item in key_foreshadows:
        lines.append(f"- {item}")
    lines.extend(["", "### 能力 / 资源快照", ""])
    for item in power_snapshot:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 六、节拍执行清单",
        "",
    ])
    for idx, beat in enumerate(beats, start=1):
        lines.extend(
            [
                f"### 节拍 {idx}《{beat['name']}》",
                "",
                f"- 预算：约 {beat['budget']} 字",
                f"- 本节功能：{beat['function']}",
                f"- 场景种子：{beat.get('scene_seed', beat['key_action'])}",
                f"- 必须发生：{beat['key_action']}",
                f"- 冲突焦点：{beat.get('conflict_focus', beat['function'])}",
                f"- 结果落点：{beat['landing']}",
                f"- 不要写成：{beat.get('taboo', '不要写成空转说明。')}",
                "",
            ]
        )
    lines.extend(["## 七、必须落地的节点", ""])
    for idx, node in enumerate(must_nodes, start=1):
        lines.append(f"- 节点 {idx}：{node}")
    lines.extend(["", "## 八、风格要求", ""])
    for item in style_rules:
        lines.append(f"- {item}")
    lines.extend(["", "## 九、关键 state 约束", ""])
    for key, value in state_constraints.items():
        lines.append(f"- {key}：{value}")
    lines.extend(
        [
            "",
            "## 十、禁忌项",
            "",
        ]
    )
    for item in taboos:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 十一、输出格式要求",
            "",
            f"- 直接输出第{chapter}章《{title}》的正文",
            "- 不输出分析说明",
            "- 保持以正文为主，不要重复提示词结构",
            "- 段落偏短，优先保证移动端阅读节奏",
            "- 每个节拍都要有真实推进，不要只做概念复述",
        ]
    )
    return "\n".join(lines) + "\n"


def render_plan_check_md(plan: dict) -> str:
    beat_budget = sum(beat["budget"] for beat in plan["beats"])
    status = "通过"
    findings = []
    if beat_budget != plan["target_words"]:
        findings.append(f"- 节拍预算合计 {beat_budget}，与目标字数 {plan['target_words']} 不一致。")
        status = "需修正"
    if not plan["must_nodes"]:
        findings.append("- 必写节点为空。")
        status = "需修正"
    if not plan["must_payoff_ids"]:
        findings.append("- 本章未显式绑定任何 must_payoff_ids，建议确认是否合理。")
    if not findings:
        findings.append("- 节拍、预算和必写节点结构完整，可进入人审。")
    return dedent(
        f"""\
        # 章节计划检查报告

        ## 一、基础信息

        - 章节号：{plan['chapter']}
        - 章节标题：{plan['title']}

        ## 二、总体结论

        - 结论：{status}
        - 节拍数：{len(plan['beats'])}
        - 预算合计：{beat_budget}

        ## 三、检查项

        {'\n'.join(findings)}
        """
    )


def load_plan_data(chapter_dir: Path) -> dict | None:
    path = chapter_dir / "plan.data.yaml"
    return load_yaml(path)


def detect_latest_draft(chapter_dir: Path) -> Path | None:
    candidates = [
        chapter_dir / "draft-v1.md",
        chapter_dir / "draft-v2-humanized.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def detect_review_target(chapter_dir: Path) -> Path | None:
    for path in [chapter_dir / "draft-v2-humanized.md", chapter_dir / "draft-v1.md"]:
        if path.exists():
            return path
    return None


def split_long_lines(text: str, limit: int = 110) -> str:
    result = []
    for paragraph in text.splitlines():
        if len(paragraph) <= limit or paragraph.startswith("#"):
            result.append(paragraph)
            continue
        current = paragraph
        while len(current) > limit:
            cut = max(current.rfind("。", 0, limit), current.rfind("，", 0, limit))
            if cut <= 0:
                cut = limit
            result.append(current[: cut + 1].strip())
            current = current[cut + 1 :].strip()
        if current:
            result.append(current)
    return "\n".join(result)


def meaningful_fragment(text: str) -> str:
    cleaned = re.sub(r"[：:，。、“”\"'（）()\-\s]", "", text)
    return cleaned[:8]


def count_cjk_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def max_paragraph_length(text: str) -> int:
    paragraphs = [len(p.strip()) for p in text.split("\n\n") if p.strip()]
    return max(paragraphs, default=0)


def find_ai_markers(text: str) -> list[str]:
    markers = [
        "极致",
        "彻底",
        "疯狂",
        "眼中闪过",
        "嘴角勾起",
        "与此同时",
        "紧接着",
        "不是",
    ]
    return [marker for marker in markers if marker in text]


def render_draft_review_md(
    *,
    chapter: int,
    title: str,
    version: str,
    conclusion: str,
    blockers: list[str],
    warnings: list[str],
    notes: list[str],
) -> str:
    lines = [
        "# 正文审稿报告",
        "",
        "## 一、基础信息",
        "",
        f"- 章节号：{chapter}",
        f"- 章节标题：{title}",
        f"- 审查版本：{version}",
        "",
        "## 二、总体结论",
        "",
        f"- 结论：{conclusion}",
        "- 简述原因：基于计划完成度、连续性、文风风险与节奏做出的自动审查结论。",
        "",
        "## 三、Blocker",
        "",
    ]
    lines.extend(render_bullets(blockers, "无"))
    lines.extend(["", "## 四、Warning", ""])
    lines.extend(render_bullets(warnings, "无"))
    lines.extend(["", "## 五、Note", ""])
    lines.extend(render_bullets(notes, "无"))
    lines.extend(
        [
            "",
            "## 六、修订建议",
            "",
            "- 先清理 Blocker，再处理 Warning。",
            "- Blocker 清零后再进入正式人审。",
        ]
    )
    return "\n".join(lines) + "\n"


def render_human_review_md(review: dict, *, title: str) -> str:
    stage_map = {
        "plan": "章节计划审核",
        "final": "正文定稿审核",
    }
    lines = [
        "# 人工审核记录",
        "",
        "## 一、基础信息",
        "",
        f"- 章节号：{review['chapter']}",
        f"- 章节标题：{title}",
        f"- 审核阶段：{stage_map.get(review['stage'], review['stage'])}",
        f"- 审核结论：{review['decision_label']}",
        f"- 审核人：{review['reviewer']}",
        f"- 审核时间：{review['reviewed_at']}",
        f"- 对应文件：{review['source_file']}",
        "",
        "## 二、审核备注",
        "",
    ]
    notes = review.get("notes", "").strip()
    lines.append(f"- {notes if notes else '无'}")
    return "\n".join(lines) + "\n"


def summarize_text(text: str, max_chars: int) -> str:
    plain = re.sub(r"^#.+$", "", text, flags=re.MULTILINE).strip().replace("\n", "")
    return plain[:max_chars] + ("..." if len(plain) > max_chars else "")


def upsert_chapter_index(chapter_index: list[dict], chapter_record: dict) -> None:
    for index, item in enumerate(chapter_index):
        if item.get("chapter_no") == chapter_record["chapter_no"]:
            chapter_index[index] = chapter_record
            return
    chapter_index.append(chapter_record)
    chapter_index.sort(key=lambda item: item.get("chapter_no", 0))


def render_state_diff_md(
    *,
    chapter: int,
    title: str,
    final_name: str,
    character_changes: list[str],
    faction_changes: list[str],
    foreshadow_changes: list[str],
    power_changes: list[str],
    no_changes: list[str],
) -> str:
    has_change = any([character_changes, faction_changes, foreshadow_changes, power_changes])
    lines = [
        "# 状态差异报告",
        "",
        "## 一、基础信息",
        "",
        f"- 章节号：{chapter}",
        f"- 章节标题：{title}",
        f"- 正式版本：{final_name}",
        "",
        "## 二、总体结论",
        "",
        f"- 本章是否引发长期状态变化：{'是' if has_change else '否'}",
        "- 简述：本报告只记录会影响后续写作判断的长期事实。",
        "",
        "## 三、角色变化",
        "",
    ]
    lines.extend(render_bullets(character_changes, "无自动检测到的角色结构变化"))
    lines.extend(["", "## 四、势力变化", ""])
    lines.extend(render_bullets(faction_changes, "无自动检测到的势力结构变化"))
    lines.extend(["", "## 五、伏笔变化", ""])
    lines.extend(render_bullets(foreshadow_changes, "无自动检测到的伏笔变化"))
    lines.extend(["", "## 六、能力 / 装备 / 资源变化", ""])
    lines.extend(render_bullets(power_changes, "无自动检测到的能力或资源结构变化"))
    lines.extend(["", "## 七、无变化项", ""])
    lines.extend(render_bullets(no_changes, "无"))
    return "\n".join(lines) + "\n"


def render_bullets(items: list[str], fallback: str) -> list[str]:
    if not items:
        return [f"- {fallback}"]
    return [f"- {item}" for item in items]


def render_plot_recap_md(chapter_index: list[dict]) -> str:
    recent = chapter_index[-5:]
    lines = ["# 剧情回顾", "", "## 一、最近章节推进", ""]
    if recent:
        for item in recent:
            lines.append(f"- 章节 {item['chapter_no']}《{item['title']}》：{item.get('summary', PLACEHOLDER)}")
    else:
        lines.append("- 暂无章节记录")

    lines.extend(["", "## 二、当前卷位置", ""])
    if recent:
        latest = recent[-1]
        lines.append(f"- 当前卷主线推进到：{latest.get('volume', PLACEHOLDER)} / Ch{latest['chapter_no']}")
    else:
        lines.append("- 当前卷主线推进到：待补充")

    lines.extend(["", "## 三、当前主要矛盾", ""])
    if recent:
        for item in recent[-2:]:
            lines.append(f"- {item.get('summary', PLACEHOLDER)}")
    else:
        lines.append("- 待补充")

    lines.extend(["", "## 四、下一步接续点", ""])
    if recent:
        lines.append(f"- {recent[-1].get('ending_hook', PLACEHOLDER)}")
    else:
        lines.append("- 待补充")
    return "\n".join(lines) + "\n"


def render_state_recap_md(characters, factions, foreshadows, power_state) -> str:
    lines = ["# 状态总览", "", "## 一、关键角色", ""]
    if characters:
        for item in characters[:8]:
            lines.append(f"- {item.get('name', PLACEHOLDER)}：{item.get('status', PLACEHOLDER)} / 最近章节 Ch{item.get('latest_chapter', 0)}")
    else:
        lines.append("- 待补充")

    lines.extend(["", "## 二、关键势力", ""])
    if factions:
        for item in factions[:8]:
            lines.append(f"- {item.get('name', PLACEHOLDER)}：{item.get('relationship_to_protagonist', PLACEHOLDER)} / 据点 {item.get('territory', PLACEHOLDER)}")
    else:
        lines.append("- 待补充")

    lines.extend(["", "## 三、关键资源 / 能力", ""])
    protagonist = power_state.get("protagonist", {}) if isinstance(power_state, dict) else {}
    lines.append(f"- 主角基础战力：{protagonist.get('baseline_power', PLACEHOLDER)}")
    for key in ["key_items", "base_or_assets", "rare_resources"]:
        values = power_state.get(key, []) if isinstance(power_state, dict) else []
        if values:
            for item in values[:3]:
                lines.append(f"- {key}：{item}")

    lines.extend(["", "## 四、未回收伏笔", ""])
    open_items = [item for item in foreshadows if item.get("current_status") in {"open", "advanced"}]
    if open_items:
        for item in open_items[:10]:
            lines.append(f"- {item.get('id', PLACEHOLDER)}：{item.get('description', PLACEHOLDER)}")
    else:
        lines.append("- 暂无未回收伏笔")
    return "\n".join(lines) + "\n"


def print_write_summary(command: str, root: Path, written: list[Path], skipped: list[Path]) -> None:
    print(f"{command} 已执行。")
    print(f"目标目录: {root}")
    if written:
        print("已写入文件:")
        for path in written:
            try:
                print(f"- {path.relative_to(root)}")
            except ValueError:
                print(f"- {path}")
    if skipped:
        print("未覆盖文件（使用 --force 可强制覆盖）:")
        for path in skipped:
            try:
                print(f"- {path.relative_to(root)}")
            except ValueError:
                print(f"- {path}")


def infer_serial_mode(length: str) -> str:
    digits = "".join(re.findall(r"\d+", length))
    if digits:
        value = int(digits)
        if "万" in length:
            if value >= 150:
                return "超长连载"
            if value >= 80:
                return "长篇连载"
            if value >= 30:
                return "中长篇"
    if "百万" in length or "100W" in length.upper():
        return "长篇连载"
    return "待确认篇幅模式"


def build_platform_guidelines(platform: str) -> dict[str, str]:
    platform_lower = platform.lower()
    if "番茄" in platform:
        return {
            "reader_profile": "偏移动端追更读者，接受信息要快、冲突要早、章末承接要强",
            "paragraph_rule": "默认短段，段落尽量控制在 1 到 3 句",
            "hook_rule": "每章结尾必须留下明确承接点，优先用危机、收益、反转驱动追更",
            "dialogue_rule": "对白要直给，少空转感慨，尽量让对白承担推进功能",
        }
    if "起点" in platform:
        return {
            "reader_profile": "偏网文核心读者，接受设定和升级体系，但要求兑现稳定",
            "paragraph_rule": "段落可比移动端略长，但关键信息仍应拆开呈现",
            "hook_rule": "章节结尾要么抛新问题，要么给新收益承诺，避免纯情绪停顿",
            "dialogue_rule": "对白可承担设定解释，但必须夹带冲突或利益变化",
        }
    if "晋江" in platform:
        return {
            "reader_profile": "偏角色关系与情绪体验驱动读者，要求角色动机稳定",
            "paragraph_rule": "保持清晰分段，情绪段可稍长，但不要失去推进",
            "hook_rule": "章末优先留下关系变化、情绪反转或新信息钩子",
            "dialogue_rule": "对白要带情绪与潜台词，避免机械解释",
        }
    if "纵横" in platform or "17k" in platform_lower:
        return {
            "reader_profile": "偏传统网文连载读者，接受体系和剧情并重",
            "paragraph_rule": "段落控制在可快速扫描范围内，信息密度优先",
            "hook_rule": "章末要保证下一章有可立即接续的动作线",
            "dialogue_rule": "对白不宜拖泥带水，要服务阵营、利益和冲突",
        }
    return {
        "reader_profile": "默认按网络连载读者处理，追求快进入、快推进、强承接",
        "paragraph_rule": "默认短段，优先适配移动端阅读",
        "hook_rule": "每章结尾必须为下一章留下明确承接理由",
        "dialogue_rule": "对白优先承担推进，而不是重复说明",
    }


def build_serial_constraints(data: InitBookInput) -> dict[str, str]:
    mode = infer_serial_mode(data.length)
    return {
        "serial_mode": mode,
        "promise_rule": f"{mode} 默认按“长期连载承诺”处理，主线必须持续服务“{data.hook}”。",
        "escalation_rule": "每一卷都必须让主角位置、资源规模或敌我强度发生可见升级。",
        "continuity_rule": "影响后续判断的事实必须进入 state，不能只留在正文语气里。",
        "audit_rule": "初始化只建立最小强约束，不替代后续人审和补充设定。",
    }


def render_premise_md(data: InitBookInput) -> str:
    platform_profile = build_platform_guidelines(data.platform)
    serial_constraints = build_serial_constraints(data)
    return dedent(
        f"""\
        # 书籍主旨

        ## 一句话概述

        - 《{data.title}》是一部面向 {data.platform} 的 {data.genre}，围绕“{data.hook}”展开，主角是 {data.protagonist}。

        ## 读者承诺

        - 核心上头点：每隔若干章节，读者都要看到“{data.hook}”带来的新收益、新代价或新危机。
        - 主追更引擎：主角围绕“{data.hook}”持续变强、争夺、反杀或改写处境。
        - 长篇模式：{serial_constraints['serial_mode']}

        ## 核心情绪价值

        - 读者看这本书主要获得什么：围绕“{data.hook}”建立长期追更动力，细化待补充。
        - 读者每卷至少应获得什么：主角地位抬升、核心矛盾升级、主卖点兑现一次。

        ## 长期主轴

        - 主线问题：主角如何依靠“{data.hook}”从当前处境一路打到下一层级。
        - 升级主轴：主角的力量、资源、人脉或阵营规模必须持续扩张，细节待补充。
        - 承诺边界：所有重要支线最终都要回流主线，不能长期脱离核心卖点。

        ## 平台定位

        - 目标平台：{data.platform}
        - 目标读者：{platform_profile['reader_profile']}
        - 核心标签：{data.genre} / 长篇连载 / 待补充
        - 阅读节奏要求：{platform_profile['paragraph_rule']}

        ## 禁止偏离项

        - 这本书绝不能写成什么样：不能偏离“{data.hook}”去写长期无关支线。
        - 禁止问题 1：不能让主角长期被动挨打却没有新的筹码增长。
        - 禁止问题 2：不能把卷末升级写成只有情绪，没有事实变化。

        ## 初始化阶段默认强约束

        - {serial_constraints['promise_rule']}
        - {serial_constraints['escalation_rule']}
        - {serial_constraints['continuity_rule']}
        - {serial_constraints['audit_rule']}
        """
    )


def render_setting_md(data: InitBookInput) -> str:
    serial_constraints = build_serial_constraints(data)
    return dedent(
        f"""\
        # 世界设定

        ## 故事背景

        - 时间背景：待补充
        - 空间背景：待补充
        - 社会环境：待补充

        ## 核心规则

        - 规则 1：主线始终服务于核心卖点“{data.hook}”
        - 规则 2：主角每次获得明显收益，都应伴随代价、门槛或更高层敌意。
        - 规则 3：能改变长期判断的设定必须可被复述成结构化事实。
        - 规则 4：同一类世界规则一旦确认，后文不得无解释改写。

        ## 力量或冲突系统

        - 力量来源：围绕“{data.hook}”建立，可在后续补齐具体机制。
        - 约束条件：收益不能无成本无限获取，细化待补充。
        - 成长路径：从当前处境起步，经由阶段性冲突完成层级提升。

        ## 冲突升级轴

        - 第一层：先解决主角的生存、起步或第一次立足问题。
        - 第二层：把个人冲突升级为资源争夺、阵营对抗或规则博弈。
        - 第三层：让主角面对更高层级敌人、系统真相或世界性压力。
        - 长篇要求：{serial_constraints['escalation_rule']}

        ## 高风险连续性事项

        - 容易写崩的设定点：如果“{data.hook}”的收益规则忽强忽弱，整本书会失去可信度。
        - 必须长期保持一致的规则：主角资源获取方式、敌我差距来源、世界基本惩罚机制。
        - 初始化假设：暂未确认的世界细节可以留白，但不能和已定主线承诺打架。
        """
    )


def render_style_rules_md(data: InitBookInput) -> str:
    tone = data.tone or PLACEHOLDER
    reference = data.reference or PLACEHOLDER
    platform_profile = build_platform_guidelines(data.platform)
    return dedent(
        f"""\
        # 文风规则

        ## 目标风格

        - 目标气质：{tone}
        - 节奏偏好：快进入、快推进、关键处停得住
        - 对话风格：对白优先承担推进与施压，不只负责解释

        ## 平台适配要求

        - 段落长度：{platform_profile['paragraph_rule']}
        - 爽点密度：每章至少要有一次明确推进或收益，不允许整章空转
        - 钩子类型偏好：{platform_profile['hook_rule']}
        - 对话使用原则：{platform_profile['dialogue_rule']}

        ## 叙事镜头要求

        - 默认采用贴近主角的近景视角，减少全知说明型长段落。
        - 重要规则优先在冲突现场显现，不优先用纯解释段告知。
        - 场景切换要服务节拍，不要为了“显得丰富”频繁跳镜头。

        ## 风格参照

        - 参考作品或风格：{reference}

        ## 禁用表达

        - 禁用词：极致、彻底、疯狂 等无信息增量副词需谨慎使用
        - 禁用句式：连续解释世界观却没有动作推进的说明段
        - 禁用套路：靠旁白宣布“很危险”“很震惊”代替真实场面

        ## 自检清单

        - 需要重点搜索和清理的表达：模板化表情、机械过渡词、假高潮式章末收束
        - 每章自检：是否真的推进了目标，是否留下了下一章承接理由
        """
    )


def render_protagonist_md(data: InitBookInput) -> str:
    return dedent(
        f"""\
        # 主角卡

        ## 基础信息

        - 姓名：{data.protagonist}
        - 年龄：待补充
        - 身份：待补充
        - 初始处境：围绕“{data.hook}”建立主线起点，细化待补充
        - 初始缺口：主角眼下最缺什么，导致他必须进入主线，待补充

        ## 核心驱动力

        - 想要什么：待补充
        - 最怕什么：待补充
        - 最不能退让的底线：待补充
        - 短期必须解决的问题：待补充

        ## 长期人物弧线

        - 这本书里主角会从什么状态成长到什么状态：待补充
        - 这条成长线必须始终与“{data.hook}”绑定，而不是平行展开
        - 每一卷结束时，主角都应获得可结构化记录的新位置、新能力或新筹码

        ## 能力与短板

        - 当前优势：待补充
        - 当前短板：待补充
        - 成长方向：待补充
        - 成长代价：待补充

        ## 人设红线

        - 绝不能出现的失真行为：不能为了推动剧情，突然违背已确认底线或智商水平
        - 主角的爽点来源必须稳定：优先来自“{data.hook}”兑现，而不是旁人降智抬轿

        ## 关系起点

        - 重要初始关系：待补充
        - 最先会牵动主线的关系：待补充

        ## 首卷必须成立的读者印象

        - 读者应该为什么持续追主角：待补充
        - 读者不应该对主角产生什么反感：待补充
        """
    )


def render_volume_outline_md(data: InitBookInput) -> str:
    serial_constraints = build_serial_constraints(data)
    return dedent(
        f"""\
        # 第一卷纲要

        ## 卷目标

        - 这一卷要完成什么：围绕“{data.hook}”建立世界、主角位置和第一阶段主线。

        ## 卷核心卖点

        - 本卷最核心的吸引力：{data.hook}
        - 本卷必须兑现一次什么承诺：主角第一次把“{data.hook}”转化为可见战果或地位变化。

        ## 卷级节奏要求

        - 开卷前段：尽快让主角进入不能回头的主问题。
        - 卷中阶段：让主角付出代价换来第一次真正扩张。
        - 卷末阶段：完成阶段性胜利，并抛出更高一级问题。
        - 连载约束：{serial_constraints['escalation_rule']}

        ## 主要阶段

        ### 阶段一

        - 目标：建立主角起点与核心冲突
        - 冲突：待补充
        - 结果：待补充
        - 读者承诺：必须让读者看清“这本书以后主要爽在哪里”

        ### 阶段二

        - 目标：扩大主线冲突与角色关系
        - 冲突：待补充
        - 结果：待补充
        - 读者承诺：必须给出第一次阶段性兑现，而不是一直预热

        ### 阶段三

        - 目标：完成第一卷收束并抛出后续钩子
        - 冲突：待补充
        - 结果：待补充
        - 读者承诺：卷末必须同时提供胜利感和继续追更理由

        ## 卷末状态

        - 主角会到达什么状态：待补充
        - 世界格局会发生什么变化：待补充
        - 给下一卷留下什么钩子：待补充

        ## 需要后续补齐的关键空白

        - 第一卷核心反派或对手结构
        - 第一卷中段最大反转
        - 第一卷卷末必须回收的承诺
        """
    )


def render_characters_yaml(data: InitBookInput) -> str:
    capability = f"主角核心能力或筹码将围绕“{data.hook}”展开，具体细节待补充"
    return dedent(
        f"""\
        - id: protagonist
          name: {data.protagonist}
          faction: self
          status: alive
          current_location: 待补充
          relationship_to_protagonist: self
          capability_summary: {capability}
          latest_chapter: 0
          open_threads:
            - 主线起点待补充
            - 第一次阶段性胜利要通过什么方式拿到，待补充
        """
    )


def render_factions_yaml() -> str:
    return dedent(
        """\
        - id: self
          name: 主角阵营
          leader: protagonist
          members_summary: 初始仅主角
          territory: 待补充
          resources:
            - 主角当前可调动资源待补充
          relationship_to_protagonist: self
          latest_change_chapter: 0
        """
    )


def render_power_state_yaml(data: InitBookInput) -> str:
    return dedent(
        f"""\
        protagonist:
          baseline_power: 待补充
          current_constraints:
            - 围绕“{data.hook}”建立能力与限制，细化待补充
            - 在未明确规则前，不允许把主角收益写成无代价无限增长

        systems_or_rules:
          - “{data.hook}”相关系统或规则待补充
          - 长期有效的世界硬规则待补充

        key_items:
          - 待补充

        companions:
          - 待补充

        base_or_assets:
          - 待补充

        rare_resources:
          - 待补充
        """
    )


def render_init_summary_md(
    data: InitBookInput,
    *,
    codename: str,
    tone: str,
    reference: str,
) -> str:
    return dedent(
        f"""\
        # 初始化摘要

        ## 一、已创建文件

        - `book/canon/premise.md`
        - `book/canon/setting.md`
        - `book/canon/style_rules.md`
        - `book/canon/characters/protagonist.md`
        - `book/canon/volumes/volume-01-outline.md`
        - `book/state/characters.yaml`
        - `book/state/factions.yaml`
        - `book/state/foreshadows.yaml`
        - `book/state/power_state.yaml`
        - `book/state/chapter_index.yaml`
        - `book/artifacts/reports/init-book-summary.md`

        ## 二、来自用户明确输入的信息

        - 书名：{data.title}
        - 题材：{data.genre}
        - 平台：{data.platform}
        - 核心卖点：{data.hook}
        - 主角定位：{data.protagonist}
        - 目标篇幅：{data.length}
        - 文风偏好：{tone}
        - 参考作品：{reference}

        ## 三、由 agent 做出的最小推断

        - 项目代称：{codename}
        - 初始化阶段只建立第一卷最小骨架，不扩写完整长篇大纲
        - 初始阵营使用 `self` 作为主角阵营占位
        - 默认按 {infer_serial_mode(data.length)} 处理，要求后续每卷都提供实际升级
        - 未被用户明确提供的规则与设定，统一保留为“待补充”

        ## 四、当前已写入的强约束

        - 主线必须持续服务核心卖点“{data.hook}”
        - 长篇连载中，主角每卷都要获得可结构化记录的新筹码
        - 影响连续性的事实必须回写 state，不能只停留在正文表达
        - 平台适配默认已写入 `style_rules.md`，后续应按实际平台再细化

        ## 五、仍待确认或补充的内容

        - 世界背景细节
        - 力量或冲突系统
        - 主角具体起点处境
        - 第一卷详细冲突与阶段结果
        - 文风禁用项和平台适配细节

        ## 六、下一步建议

        - 先审核这次初始化结果
        - 优先补齐会影响连续性的硬信息，而不是追求一次补完整本大纲
        - 修正你不认同的最小假设
        - 确认后再进入第 1 章的 `plan-chapter`
        """
    )


if __name__ == "__main__":
    raise SystemExit(main())
