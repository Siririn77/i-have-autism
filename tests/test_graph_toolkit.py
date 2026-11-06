"""The graph toolkit: parsing, checking, stats, plan compilation, diff, scaffolding.

The scripts are the contract — a rule that cannot be checked is a wish. Each test here fails when a
script silently stops noticing something.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "i-have-autism" / "scripts"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "graph-mini.md"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"нет модуля {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(SCRIPTS))
graph_lib = load_module("graph_lib")
check_graph = load_module("check_graph")
graph_stats = load_module("graph_stats")
graph_to_plan = load_module("graph_to_plan")
graph_diff = load_module("graph_diff")


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
        self.graph.nodes["N3"] = self.graph.nodes["N3"].__class__(
            **{**self.graph.nodes["N3"].__dict__, "anchor": ""}
        )
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
        text = graph_to_plan.build(graph_lib.load(FIXTURE), 40)
        self.assertIn("TODO", text)


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
            [sys.executable, str(SCRIPTS / "check_graph.py"), str(FIXTURE)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_check_cli_exits_one_on_a_broken_graph(self):
        broken = FIXTURE.read_text(encoding="utf-8").replace("| N1 | causes | N2 |", "| N1 | related | N2 |")
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
            handle.write(broken)
            path = handle.name
        completed = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_graph.py"), path],
            capture_output=True,
            text=True,
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
            parsed = graph_lib.load(target)
            self.assertEqual(len(parsed.questions), 5)


if __name__ == "__main__":
    unittest.main()
