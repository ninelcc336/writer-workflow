from __future__ import annotations

import argparse
import re
import shutil
import sys
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
    volume = args.volume
    target_words = args.target_words
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
        ending_type=args.ending_type,
    )
    plan_data = {
        "chapter": args.chapter,
        "title": chapter_title,
        "volume": volume,
        "goal": chapter_goal,
        "target_words": target_words,
        "ending_type": args.ending_type,
        "ending_hint": ending_hint,
        "must_payoff_ids": must_payoff_ids,
        "must_nodes": brief_must_nodes or [
            f"{protagonist_name}必须正式进入本章核心冲突",
            "本章关键矛盾必须完成至少一次实质推进",
            f"结尾必须形成“{args.ending_type}”的明确落点",
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


def run_draft_chapter(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    chapter_dir = get_chapter_dir(root, args.chapter)
    plan_data = load_plan_data(chapter_dir)
    if not plan_data:
        print("draft-chapter 无法执行：缺少 plan.data.yaml，请先执行 plan-chapter。", file=sys.stderr)
        return 1

    protagonist_name = extract_protagonist_name(root) or "主角"
    title = plan_data["title"]
    goal = plan_data["goal"]
    ending_hint = plan_data.get("ending_hint", "待补充")
    beats = plan_data["beats"]
    draft_parts = [f"# 第{args.chapter}章：{title}", ""]
    draft_parts.append(f"{protagonist_name}很清楚，这一章真正要解决的，是“{goal}”。")
    draft_parts.append("")

    for index, beat in enumerate(beats, start=1):
        draft_parts.append(
            f"{protagonist_name}先把注意力放在“{beat['name']}”上。{beat['key_action']}。"
            f"这一节的功能是{beat['function']}，所以场面必须朝着“{beat['landing']}”推进。"
        )
        draft_parts.append("")
        draft_parts.append(
            f"第{index}个节拍里，局势不会只是表面热闹。{protagonist_name}需要在这一段里真正推动矛盾，"
            f"并把读者带到下一个动作点。"
        )
        draft_parts.append("")

    draft_parts.append(f"本章结尾应落在：{plan_data['ending_type']}。")
    draft_parts.append(f"具体收束方向：{ending_hint}。")
    draft_text = "\n".join(draft_parts).strip() + "\n"

    draft_path = chapter_dir / "draft-v1.md"
    draft_data_path = chapter_dir / "draft-v1.data.yaml"
    metadata = {
        "chapter": args.chapter,
        "title": title,
        "source_plan": "plan.data.yaml",
        "version": "draft-v1",
        "beat_count": len(beats),
        "target_words": plan_data["target_words"],
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
    source_path = Path(args.source_file).resolve() if args.source_file else detect_latest_draft(chapter_dir)
    if not source_path or not source_path.exists():
        print("humanize-chapter 无法执行：找不到草稿文件。", file=sys.stderr)
        return 1

    text = source_path.read_text(encoding="utf-8")
    text = text.replace("这一节的功能是", "")
    text = text.replace("第", "第")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("必须朝着“", "朝着“")
    text = split_long_lines(text)
    text = text.replace("本章结尾应落在：", "章末落点：")
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

    if not blockers and not warnings:
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

    text = final_path.read_text(encoding="utf-8")
    characters = load_yaml(root / "book" / "state" / "characters.yaml") or []
    factions = load_yaml(root / "book" / "state" / "factions.yaml") or []
    foreshadows = load_yaml(root / "book" / "state" / "foreshadows.yaml") or []
    power_state = load_yaml(root / "book" / "state" / "power_state.yaml") or {}
    chapter_index = load_yaml(root / "book" / "state" / "chapter_index.yaml") or []

    character_changes = []
    for item in characters:
        name = str(item.get("name", ""))
        if name and name != PLACEHOLDER and name in text:
            old = item.get("latest_chapter", 0)
            item["latest_chapter"] = args.chapter
            if old != args.chapter:
                character_changes.append(f"{name} 最近出场章节更新为 Ch{args.chapter}")

    payoff_ids = plan_data.get("must_payoff_ids", [])
    foreshadow_changes = []
    if payoff_ids:
        for payoff_id in payoff_ids:
            matched = False
            for item in foreshadows:
                if item.get("id") == payoff_id:
                    item["current_status"] = "advanced"
                    item["last_progress_chapter"] = args.chapter
                    foreshadow_changes.append(f"伏笔 {payoff_id} 标记为 advanced")
                    matched = True
                    break
            if not matched:
                foreshadows.append(
                    {
                        "id": payoff_id,
                        "description": f"由章节计划引入的跟踪项：{payoff_id}",
                        "introduced_in": args.chapter,
                        "current_status": "advanced",
                        "related_characters": [],
                        "expected_payoff_window": "待补充",
                        "last_progress_chapter": args.chapter,
                    }
                )
                foreshadow_changes.append(f"新增伏笔跟踪项 {payoff_id}")

    hook_id = f"hook-ch{format_chapter(args.chapter)}"
    ending_hint = plan_data.get("ending_hint", "")
    foreshadows.append(
        {
            "id": hook_id,
            "description": ending_hint or plan_data.get("ending_type", "本章章末钩子"),
            "introduced_in": args.chapter,
            "current_status": "open",
            "related_characters": [],
            "expected_payoff_window": "下一章",
            "last_progress_chapter": args.chapter,
        }
    )
    foreshadow_changes.append(f"新增章末钩子追踪项 {hook_id}")

    summary = summarize_text(text, 80)
    chapter_record = {
        "chapter_no": args.chapter,
        "title": plan_data["title"],
        "volume": plan_data["volume"],
        "status": "final",
        "summary": summary,
        "must_payoff_ids": payoff_ids,
        "new_state_changes": character_changes + foreshadow_changes,
        "ending_hook": ending_hint or plan_data.get("ending_type", "待补充"),
    }
    upsert_chapter_index(chapter_index, chapter_record)

    write_yaml(root / "book" / "state" / "characters.yaml", characters)
    write_yaml(root / "book" / "state" / "factions.yaml", factions)
    write_yaml(root / "book" / "state" / "foreshadows.yaml", foreshadows)
    write_yaml(root / "book" / "state" / "power_state.yaml", power_state)
    write_yaml(root / "book" / "state" / "chapter_index.yaml", chapter_index)

    no_changes = []
    if not character_changes:
        no_changes.append("角色状态未自动检测到结构性变化")
    if not foreshadow_changes:
        no_changes.append("伏笔状态未自动检测到变化")
    if not factions:
        no_changes.append("暂无势力信息")

    report_md = render_state_diff_md(
        chapter=args.chapter,
        title=plan_data["title"],
        final_name=final_path.name,
        character_changes=character_changes,
        faction_changes=[],
        foreshadow_changes=foreshadow_changes,
        power_changes=[],
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
    characters = load_yaml(root / "book" / "state" / "characters.yaml")
    premise = root / "book" / "canon" / "premise.md"
    setting = root / "book" / "canon" / "setting.md"
    if not premise.exists() or not setting.exists():
        return False, "canon 基础文件缺失。"
    if not characters:
        return False, "characters.yaml 缺失或为空。"
    protagonist = characters[0]
    if protagonist.get("name") in (None, "", PLACEHOLDER):
        return False, "主角名称仍是占位值。"
    return True, ""


def load_brief_text(args: argparse.Namespace) -> str | None:
    if args.brief_file:
        return Path(args.brief_file).read_text(encoding="utf-8")
    return args.brief_text


def parse_brief_text(text: str) -> dict:
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
        raw_beats = beat_suggestions[:4]
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
        if index == 0:
            function = "建立本章起点并快速挂上核心冲突"
            action = f"{protagonist_name}必须在开场就卷入“{chapter_goal}”"
            landing = "把读者带进本章主问题"
        elif index == len(raw_beats) - 1:
            function = "完成本章收束并形成下一步承接"
            action = f"让{chapter_title}的主要矛盾完成当前阶段收束"
            landing = f"形成“{ending_type}”的明确结尾"
        else:
            function = "推进核心矛盾并增加有效信息量"
            action = f"{protagonist_name}需要围绕“{chapter_goal}”做出实质动作"
            landing = "把局势推向下一节拍"
        beats.append(
            {
                "name": name,
                "function": function,
                "budget": budgets[index],
                "key_action": action,
                "landing": landing,
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
    else:
        ratios = [0.2, 0.3, 0.3, 0.2]
    budgets = [int(target_words * ratio) for ratio in ratios[:beat_count]]
    diff = target_words - sum(budgets)
    budgets[-1] += diff
    return budgets


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
        chapter_dir / "draft-v2-humanized.md",
        chapter_dir / "draft-v1.md",
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


def render_premise_md(data: InitBookInput) -> str:
    return dedent(
        f"""\
        # 书籍主旨

        ## 一句话概述

        - 《{data.title}》是一部面向 {data.platform} 的 {data.genre}，围绕“{data.hook}”展开，主角是 {data.protagonist}。

        ## 核心情绪价值

        - 读者看这本书主要获得什么：围绕“{data.hook}”建立长期追更动力，细化待补充。

        ## 平台定位

        - 目标平台：{data.platform}
        - 目标读者：待补充
        - 核心标签：{data.genre} / 待补充

        ## 禁止偏离项

        - 这本书绝不能写成什么样：待补充
        """
    )


def render_setting_md(data: InitBookInput) -> str:
    return dedent(
        f"""\
        # 世界设定

        ## 故事背景

        - 时间背景：待补充
        - 空间背景：待补充
        - 社会环境：待补充

        ## 核心规则

        - 规则 1：主线始终服务于核心卖点“{data.hook}”
        - 规则 2：关键世界规则待补充
        - 规则 3：关键成长或冲突约束待补充

        ## 力量或冲突系统

        - 力量来源：待补充
        - 约束条件：待补充
        - 成长路径：待补充

        ## 高风险连续性事项

        - 容易写崩的设定点：待补充
        - 必须长期保持一致的规则：待补充
        """
    )


def render_style_rules_md(data: InitBookInput) -> str:
    tone = data.tone or PLACEHOLDER
    reference = data.reference or PLACEHOLDER
    return dedent(
        f"""\
        # 文风规则

        ## 目标风格

        - 目标气质：{tone}
        - 节奏偏好：待补充
        - 对话风格：待补充

        ## 平台适配要求

        - 段落长度：适配 {data.platform}，默认偏短段
        - 爽点密度：待补充
        - 钩子类型偏好：待补充

        ## 风格参照

        - 参考作品或风格：{reference}

        ## 禁用表达

        - 禁用词：待补充
        - 禁用句式：待补充
        - 禁用套路：待补充

        ## 自检清单

        - 需要重点搜索和清理的表达：待补充
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

        ## 核心驱动力

        - 想要什么：待补充
        - 最怕什么：待补充
        - 最不能退让的底线：待补充

        ## 能力与短板

        - 当前优势：待补充
        - 当前短板：待补充
        - 成长方向：待补充

        ## 人设红线

        - 绝不能出现的失真行为：待补充

        ## 关系起点

        - 重要初始关系：待补充
        """
    )


def render_volume_outline_md(data: InitBookInput) -> str:
    return dedent(
        f"""\
        # 第一卷纲要

        ## 卷目标

        - 这一卷要完成什么：围绕“{data.hook}”建立世界、主角位置和第一阶段主线。

        ## 卷核心卖点

        - 本卷最核心的吸引力：{data.hook}

        ## 主要阶段

        ### 阶段一

        - 目标：建立主角起点与核心冲突
        - 冲突：待补充
        - 结果：待补充

        ### 阶段二

        - 目标：扩大主线冲突与角色关系
        - 冲突：待补充
        - 结果：待补充

        ### 阶段三

        - 目标：完成第一卷收束并抛出后续钩子
        - 冲突：待补充
        - 结果：待补充

        ## 卷末状态

        - 主角会到达什么状态：待补充
        - 世界格局会发生什么变化：待补充
        - 给下一卷留下什么钩子：待补充
        """
    )


def render_characters_yaml(data: InitBookInput) -> str:
    capability = f"围绕“{data.hook}”展开，细化待补充"
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
            - 待补充
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

        systems_or_rules:
          - 待补充

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
        - 未被用户明确提供的规则与设定，统一保留为“待补充”

        ## 四、仍待确认或补充的内容

        - 世界背景细节
        - 力量或冲突系统
        - 主角具体起点处境
        - 第一卷详细冲突与阶段结果
        - 文风禁用项和平台适配细节

        ## 五、下一步建议

        - 先审核这次初始化结果
        - 修正你不认同的最小假设
        - 确认后再进入第 1 章的 `plan-chapter`
        """
    )


if __name__ == "__main__":
    raise SystemExit(main())
