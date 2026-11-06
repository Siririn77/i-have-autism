"""The graph toolkit: parsing, checking, stats, plan compilation, diff, expansion, clouds.

The scripts are the contract — a rule that cannot be checked is a wish. Each test here fails when a
script silently stops noticing something.
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "i-have-autism" / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph-mini.md"
AGGRESSIVE = Path(__file__).resolve().parent / "fixtures" / "graph-aggressive.md"

sys.path.insert(0, str(SCRIPTS))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"нет модуля {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


graph_lib = load_module("graph_lib")
check_graph = load_module("check_graph")
graph_stats = load_module("graph_stats")
graph_to_plan = load_module("graph_to_plan")
graph_diff = load_module("graph_diff")
graph_expand = load_module("graph_expand")
cloud_lib = load_module("cloud_lib")


def _cloud() -> list[str]:
    return [
        "### Облако",
        "- ядро: первое",
        "| элемент | связь | с чем |",
        "|---|---|---|",
        "| первое | включает | второе |",
        "| второе | вызывает | третье |",
        "",
    ]


def _filled_expansion(graph, skip: tuple[str, ...] = ()) -> str:
    parts = []
    for title, fields in graph_expand.expected_sections(graph).items():
        if any(title.startswith(prefix) for prefix in skip):
            continue
        parts.append(f"## {title}")
        if title.startswith("N"):
            parts.extend(_cloud())
        for field in fields:
            parts.append(f"- {field}: содержание")
        parts.append("")
    return "\n".join(parts)


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.graph = graph_lib.load(FIXTURE)

    def test_nodes_and_questions_are_parsed(self):
        self.assertEqual(len(self.graph.nodes), 6)
        self.assertEqual(len(self.graph.questions), 2)
        self.assertEqual(len(self.graph.edges), 12)

    def test_node_fields_land_in_the_right_attributes(self):
        node = self.graph.nodes["N2"]
        self.assertEqual(node.axis, "причины")
        self.assertEqual(node.anchor, "архив, дело 2")
        self.assertEqual(node.when, "1902")

    def test_mapping_is_parsed(self):
        self.assertEqual(self.graph.mapping[0][2], ["N1", "N2", "N3"])

    def test_wrong_column_count_is_named(self):
        broken = FIXTURE.read_text(encoding="utf-8").replace(
            "| N1 | первое событие | причины | задаёт тон | архив, дело 1 | 1901 |",
            "| N1 | первое событие | причины | задаёт тон | 1901 |",
        )
        with self.assertRaises(graph_lib.ParseError):
            graph_lib.parse(broken, "broken")


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.graph = graph_lib.load(FIXTURE)

    def test_fixture_is_clean(self):
        self.assertEqual(check_graph.check(self.graph), [])

    def test_empty_anchor_is_a_defect(self):
        node = self.graph.nodes["N3"]
        self.graph.nodes["N3"] = node.__class__(**{**node.__dict__, "anchor": ""})
        problems = check_graph.check(self.graph)
        self.assertTrue(any("подтверждено" in p for p in problems), problems)

    def test_duplicate_label_is_a_defect(self):
        node = self.graph.nodes["N2"]
        self.graph.nodes["N2"] = node.__class__(**{**node.__dict__, "label": "Первое"})
        problems = check_graph.check(self.graph)
        self.assertTrue(any("подпись" in p for p in problems), problems)

    def test_cause_cycle_is_a_defect(self):
        self.graph.edges.append(graph_lib.Edge("N3", "causes", "N1", "обратная петля"))
        problems = check_graph.check(self.graph)
        self.assertTrue(any("цикл" in p for p in problems), problems)

    def test_question_with_one_answer_is_thin(self):
        self.graph.edges = [e for e in self.graph.edges if not (e.src == "Q2" and e.dst in ("N5", "N6"))]
        problems = check_graph.check(self.graph)
        self.assertTrue(any("недоисследован" in p for p in problems), problems)

    def test_thin_axis_is_reported(self):
        node = self.graph.nodes["N6"]
        self.graph.nodes["N6"] = node.__class__(**{**node.__dict__, "axis": "третья ось"})
        problems = check_graph.check(self.graph)
        self.assertTrue(any("третья ось" in p for p in problems), problems)

    def test_unknown_edge_type_is_a_defect(self):
        self.graph.edges.append(graph_lib.Edge("N1", "related", "N4", "просто рядом"))
        problems = check_graph.check(self.graph)
        self.assertTrue(any("related" in p for p in problems), problems)

    def test_drawing_that_disagrees_with_the_table_is_a_defect(self):
        self.graph.mermaid_edges = [("N1", "causes", "N9")]
        problems = check_graph.check(self.graph)
        self.assertTrue(any("не нарисовано" in p or "нет в таблице" in p for p in problems), problems)


class StatsTest(unittest.TestCase):
    def test_report_counts_answers_and_axes(self):
        report = graph_stats.report(graph_lib.load(FIXTURE))
        self.assertEqual(report["nodes"], 6)
        self.assertEqual([q["answers"] for q in report["questions"]], [3, 3])
        self.assertEqual([a["nodes"] for a in report["axes"]], [3, 3])

    def test_unmapped_nodes_are_listed_when_mapping_is_partial(self):
        graph = graph_lib.load(FIXTURE)
        graph.mapping = [("1", "начало", ["N1", "N2", "N3"])]
        report = graph_stats.report(graph)
        self.assertEqual(report["unmapped_nodes"], ["N4", "N5", "N6"])


class PlanCompileTest(unittest.TestCase):
    def test_plan_has_one_unit_per_mapping_row_and_a_gate(self):
        text = graph_to_plan.build(graph_lib.load(FIXTURE), 40)
        self.assertIn("| 1 | начало | N1, N2, N3 |", text)
        self.assertIn("| 2 | итог | N4, N5, N6 |", text)
        self.assertIn("N6 ⊥ N4", text)
        self.assertIn("Журнал расхождений", text)

    def test_plan_marks_placeholders_so_they_cannot_be_mistaken_for_work(self):
        self.assertIn("TODO", graph_to_plan.build(graph_lib.load(FIXTURE), 40))


class DiffTest(unittest.TestCase):
    def test_added_node_and_edge_are_reported(self):
        old = graph_lib.load(FIXTURE)
        new = graph_lib.load(FIXTURE)
        new.nodes["N7"] = graph_lib.Node("N7", "Седьмое", "седьмое", "следствия", "новое", "архив", "1907")
        new.edges.append(graph_lib.Edge("N6", "causes", "N7", "продолжение"))
        result = graph_diff.diff(old, new)
        self.assertEqual(result["nodes_added"], ["N7"])
        self.assertIn("N6 -causes-> N7", result["edges_added"])

    def test_identical_graphs_differ_in_nothing(self):
        self.assertFalse(any(graph_diff.diff(graph_lib.load(FIXTURE), graph_lib.load(FIXTURE)).values()))


class CliTest(unittest.TestCase):
    def test_check_cli_exits_zero_on_a_clean_graph(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_graph.py"), str(FIXTURE)], capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_check_cli_exits_one_on_a_broken_graph(self):
        broken = FIXTURE.read_text(encoding="utf-8").replace("| N1 | causes | N2 |", "| N1 | related | N2 |")
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
            handle.write(broken)
            path = handle.name
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_graph.py"), path], capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("related", completed.stdout)

    def test_new_cli_writes_a_skeleton_that_parses(self):
        with tempfile.TemporaryDirectory() as workdir:
            target = Path(workdir) / "graph.md"
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "graph_new.py"), "тест", "--kind", "code", "--out", str(target)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(len(graph_lib.load(target).questions), 5)


class AggressiveModeTest(unittest.TestCase):
    def setUp(self):
        self.graph = graph_lib.load(AGGRESSIVE)

    def test_matrix_and_register_are_parsed(self):
        self.assertEqual(self.graph.stages, ["часть 1", "часть 2"])
        self.assertEqual(len(self.graph.matrix), 2)
        self.assertEqual(len(self.graph.out_of_scope), 1)
        self.assertTrue(graph_lib.is_aggressive(self.graph))

    def test_aggressive_fixture_is_clean(self):
        self.assertEqual(check_graph.check(self.graph) + check_graph.check_aggressive(self.graph), [])

    def test_node_outside_units_and_register_is_a_defect(self):
        self.graph.mapping = [("1", "начало", ["N1", "N2", "N3"])]
        problems = check_graph.check_aggressive(self.graph)
        self.assertTrue(any("молчание запрещено" in p for p in problems), problems)

    def test_empty_matrix_cell_is_a_hole(self):
        self.graph.matrix[0] = ("причины", ["N1, N2", ""])
        problems = check_graph.check_aggressive(self.graph)
        self.assertTrue(any("дыра в покрытии" in p for p in problems), problems)

    def test_refusal_needs_a_register_entry(self):
        self.graph.matrix[0] = ("причины", ["N1, N2", "не относится"])
        problems = check_graph.check_aggressive(self.graph)
        self.assertTrue(any("отказ без записи" in p for p in problems), problems)

    def test_refusal_with_entry_is_accepted(self):
        self.graph.matrix[0] = ("причины", ["N1, N2", "не относится"])
        self.graph.out_of_scope.append(("причины × часть 2", "не относится", "ось закрыта в части 1", "—"))
        problems = check_graph.check_aggressive(self.graph)
        self.assertFalse(any("причины × часть 2" in p for p in problems), problems)

    def test_register_status_must_be_known(self):
        self.graph.out_of_scope[0] = ("последствия", "потом как-нибудь", "нет времени", "никуда")
        problems = check_graph.check_aggressive(self.graph)
        self.assertTrue(any("не из" in p for p in problems), problems)

    def test_plan_carries_the_register_and_the_matrix(self):
        text = graph_to_plan.build(self.graph, 40)
        self.assertIn("реестр", text)
        self.assertIn("последствия для третьих стран", text)
        self.assertIn("Матрица покрытия", text)


class ExpansionTest(unittest.TestCase):
    def setUp(self):
        self.graph = graph_lib.load(FIXTURE)
        self.skeleton = graph_expand.skeleton(self.graph)

    def test_skeleton_has_a_section_for_every_node_edge_and_axis(self):
        sections = graph_expand.parse_expansion(self.skeleton)
        for node_id, node in self.graph.nodes.items():
            self.assertIn(f"{node_id} «{node.label}»", sections)
        self.assertIn("Ось «причины»", sections)
        self.assertIn("Ребро N1 -causes-> N2", sections)

    def test_answers_edges_need_no_mechanism(self):
        sections = graph_expand.parse_expansion(self.skeleton)
        self.assertNotIn("Ребро Q1 -answers-> N1", sections)

    def test_composition_is_no_longer_a_flat_field(self):
        self.assertNotIn("входит", graph_expand.NODE_FIELDS)

    def test_empty_skeleton_is_not_an_expansion(self):
        problems = graph_expand.check(self.graph, self.skeleton)
        self.assertGreater(len(problems), 20)
        self.assertTrue(any("не заполнено" in p for p in problems), problems)

    def test_filled_expansion_passes(self):
        self.assertEqual(graph_expand.check(self.graph, _filled_expansion(self.graph)), [])

    def test_missing_node_section_is_named(self):
        problems = graph_expand.check(self.graph, _filled_expansion(self.graph, skip=("N3 ",)))
        self.assertTrue(any("N3" in p and "нет расшифровки" in p for p in problems), problems)

    def test_section_that_the_graph_does_not_have_is_a_defect(self):
        text = _filled_expansion(self.graph) + "\n## N99 «Выдуманный узел»\n- чем доказано: ничего\n"
        problems = graph_expand.check(self.graph, text)
        self.assertTrue(any("N99" in p for p in problems), problems)


class CloudTest(unittest.TestCase):
    def test_cloud_parses_core_elements_and_edges(self):
        cloud = cloud_lib.parse(
            "- ядро: A\n| элемент | связь | с чем |\n|---|---|---|\n| A | включает | B |\n| B | вызывает | C |"
        )
        self.assertEqual(cloud.core, "A")
        self.assertEqual(cloud.elements, ["A", "B", "C"])
        self.assertEqual(cloud.edges[1], ("B", "вызывает", "C"))

    def test_cloud_needs_a_core(self):
        cloud = cloud_lib.parse("| A | включает | B |\n| B | включает | C |")
        self.assertTrue(any("ядро" in p for p in cloud_lib.check(cloud)))

    def test_two_elements_are_a_note_not_a_cloud(self):
        cloud = cloud_lib.parse("- ядро: A\n| A | включает | B |")
        self.assertTrue(any("записка" in p for p in cloud_lib.check(cloud)))

    def test_unknown_relation_is_named(self):
        cloud = cloud_lib.parse("- ядро: A\n| A | связан с | B |\n| B | включает | C |")
        self.assertTrue(any("не из списка" in p for p in cloud_lib.check(cloud)))

    def test_self_edge_is_a_defect(self):
        cloud = cloud_lib.parse("- ядро: A\n| A | включает | A |\n| A | включает | B |\n| B | включает | C |")
        self.assertTrue(any("сам с собой" in p for p in cloud_lib.check(cloud)))

    def test_island_is_a_defect(self):
        cloud = cloud_lib.parse("- ядро: A\n| A | включает | B |\n| B | включает | C |\n| D | включает | E |")
        self.assertTrue(any("остров" in p for p in cloud_lib.check(cloud)))

    def test_too_many_elements_is_a_defect(self):
        rows = "\n".join(f"| A | включает | e{i} |" for i in range(10))
        cloud = cloud_lib.parse("- ядро: A\n" + rows)
        self.assertTrue(any("пределе" in p for p in cloud_lib.check(cloud)))

    def test_stats_count_relations(self):
        cloud = cloud_lib.parse("- ядро: A\n| A | включает | B |\n| B | вызывает | C |")
        self.assertEqual(cloud_lib.stats(cloud)["relations"], {"включает": 1, "вызывает": 1})

    def test_node_without_a_cloud_fails_the_expansion(self):
        graph = graph_lib.load(FIXTURE)
        text = _filled_expansion(graph).replace("### Облако", "### Не облако")
        problems = graph_expand.check(graph, text)
        self.assertTrue(any("ядро" in p or "ни одной связи" in p for p in problems), problems)

    def test_inline_cloud_is_read_as_a_star_from_the_core(self):
        block = (
            "**Ядро:** прогнозы условны.\n"
            "**Облако:** 1,91 млн к 2050 — *доказательство*; 39 млн кумулятивно — *включает*;"
            " 10 млн к 2050 — *противопоставлен*; сценарии — *противопоставлен*."
        )
        cloud = cloud_lib.parse_inline(block)
        self.assertEqual(cloud.core, "прогнозы условны")
        self.assertEqual(len(cloud.elements), 5)
        self.assertEqual(cloud.edges[0], ("прогнозы условны", "доказательство", "1,91 млн к 2050"))
        self.assertEqual(cloud_lib.check(cloud), [])

    def test_inline_cloud_with_a_bad_verb_is_still_rejected(self):
        block = "**Ядро:** x.\n**Облако:** a — *связано*; b — *включает*; c — *включает*."
        self.assertTrue(any("не из списка" in p for p in cloud_lib.check(cloud_lib.parse_inline(block))))


if __name__ == "__main__":
    unittest.main()
