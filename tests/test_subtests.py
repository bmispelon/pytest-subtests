from __future__ import annotations

import sys
from pathlib import Path

import pytest

IS_PY311 = sys.version_info[:2] >= (3, 11)

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


@pytest.mark.parametrize("mode", ["normal", "xdist"])
class TestFixture:
    """
    Tests for ``subtests`` fixture.
    """

    @pytest.fixture
    def simple_script(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        assert i % 2 == 0
        """
        )

    def test_simple_terminal_normal(
        self,
        simple_script: None,
        pytester: pytest.Pytester,
        mode: Literal["normal", "xdist"],
    ) -> None:
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1")
            expected_lines = ["1 worker [1 item]"]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "* 2 failed, 1 passed, 3 subtests passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_simple_terminal_verbose(
        self,
        simple_script: None,
        pytester: pytest.Pytester,
        mode: Literal["normal", "xdist"],
    ) -> None:
        if mode == "normal":
            result = pytester.runpytest("-v")
            expected_lines = [
                "*collected 1 item",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=0) SUBPASS *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=1) SUBFAIL *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=2) SUBPASS *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=3) SUBFAIL *100%*",
                "test_simple_terminal_verbose.py::test_foo [[]custom[]] (i=4) SUBPASS *100%*",
                "test_simple_terminal_verbose.py::test_foo PASSED *100%*",
            ]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1", "-v")
            expected_lines = [
                "1 worker [1 item]",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
            ]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "* 2 failed, 1 passed, 3 subtests passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_skip(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        if i % 2 == 0:
                            pytest.skip('even number')
        """
        )
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1")
            expected_lines = ["1 worker [1 item]"]
        expected_lines += ["* 1 passed, 3 skipped, 2 subtests passed in *"]
        result.stdout.fnmatch_lines(expected_lines)

    def test_xfail(
        self, pytester: pytest.Pytester, mode: Literal["normal", "xdist"]
    ) -> None:
        pytester.makepyfile(
            """
            import pytest
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        if i % 2 == 0:
                            pytest.xfail('even number')
        """
        )
        if mode == "normal":
            result = pytester.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            assert mode == "xdist"
            pytest.importorskip("xdist")
            result = pytester.runpytest("-n1")
            expected_lines = ["1 worker [1 item]"]
        expected_lines += ["* 1 passed, 3 xfailed, 2 subtests passed in *"]
        result.stdout.fnmatch_lines(expected_lines)


class TestSubTest:
    """
    Test Test.subTest functionality.
    """

    @pytest.fixture
    def simple_script(self, pytester: pytest.Pytester) -> Path:
        return pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            self.assertEqual(i % 2, 0)

            if __name__ == '__main__':
                main()
        """
        )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_normal(
        self,
        simple_script: Path,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        suffix = ".test_foo" if IS_PY311 else ""
        if runner == "unittest":
            result = pytester.run(sys.executable, simple_script)
            result.stderr.fnmatch_lines(
                [
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = pytester.runpytest(simple_script)
                expected_lines = ["collected 1 item"]
            else:
                assert runner == "pytest-xdist"
                pytest.importorskip("xdist")
                result = pytester.runpytest(simple_script, "-n1")
                expected_lines = ["1 worker [1 item]"]
            result.stdout.fnmatch_lines(
                expected_lines
                + [
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_verbose(
        self,
        simple_script: Path,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        suffix = ".test_foo" if IS_PY311 else ""
        if runner == "unittest":
            result = pytester.run(sys.executable, simple_script, "-v")
            result.stderr.fnmatch_lines(
                [
                    f"test_foo (__main__.T{suffix}) ... ",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    f"FAIL: test_foo (__main__.T{suffix}) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = pytester.runpytest(simple_script, "-v")
                expected_lines = [
                    "*collected 1 item",
                    "test_simple_terminal_verbose.py::T::test_foo [[]custom[]] (i=1) SUBFAIL *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo [[]custom[]] (i=3) SUBFAIL *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo PASSED *100%*",
                ]
            else:
                assert runner == "pytest-xdist"
                pytest.importorskip("xdist")
                result = pytester.runpytest(simple_script, "-n1", "-v")
                expected_lines = [
                    "1 worker [1 item]",
                    "*gw0*100%* SUBFAIL test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* SUBFAIL test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* PASSED test_simple_terminal_verbose.py::T::test_foo*",
                ]
            result.stdout.fnmatch_lines(
                expected_lines
                + [
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_skip(
        self,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        p = pytester.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                self.skipTest('even number')

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            result.stderr.fnmatch_lines(["Ran 1 test in *", "OK (skipped=3)"])
        else:
            pytest.xfail("Not producing the expected results (#5)")
            result = pytester.runpytest(p)  # type:ignore[unreachable]
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 skipped, 1 passed in *"]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    @pytest.mark.xfail(reason="Not producing the expected results (#5)")
    def test_xfail(
        self,
        pytester: pytest.Pytester,
        runner: Literal["unittest", "pytest-normal", "pytest-xdist"],
    ) -> None:
        p = pytester.makepyfile(
            """
            import pytest
            from unittest import expectedFailure, TestCase, main

            class T(TestCase):
                @expectedFailure
                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                raise pytest.xfail('even number')

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = pytester.runpython(p)
            result.stderr.fnmatch_lines(["Ran 1 test in *", "OK (expected failures=3)"])
        else:
            result = pytester.runpytest(p)
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 xfailed, 1 passed in *"]
            )


class TestCapture:
    def create_file(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
                    import sys
                    def test(subtests):
                        print()
                        print('start test')

                        with subtests.test(i='A'):
                            print("hello stdout A")
                            print("hello stderr A", file=sys.stderr)
                            assert 0

                        with subtests.test(i='B'):
                            print("hello stdout B")
                            print("hello stderr B", file=sys.stderr)
                            assert 0

                        print('end test')
                        assert 0
                """
        )

    def test_capturing(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*__ test (i='A') __*",
                "*Captured stdout call*",
                "hello stdout A",
                "*Captured stderr call*",
                "hello stderr A",
                "*__ test (i='B') __*",
                "*Captured stdout call*",
                "hello stdout B",
                "*Captured stderr call*",
                "hello stderr B",
                "*__ test __*",
                "*Captured stdout call*",
                "start test",
                "end test",
            ]
        )

    def test_no_capture(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest("-s")
        result.stdout.fnmatch_lines(
            [
                "start test",
                "hello stdout A",
                "uhello stdout B",
                "uend test",
                "*__ test (i='A') __*",
                "*__ test (i='B') __*",
                "*__ test __*",
            ]
        )
        result.stderr.fnmatch_lines(["hello stderr A", "hello stderr B"])

    @pytest.mark.parametrize("fixture", ["capsys", "capfd"])
    def test_capture_with_fixture(
        self, pytester: pytest.Pytester, fixture: Literal["capsys", "capfd"]
    ) -> None:
        pytester.makepyfile(
            rf"""
            import sys

            def test(subtests, {fixture}):
                print('start test')

                with subtests.test(i='A'):
                    print("hello stdout A")
                    print("hello stderr A", file=sys.stderr)

                out, err = {fixture}.readouterr()
                assert out == 'start test\nhello stdout A\n'
                assert err == 'hello stderr A\n'
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*1 passed*",
            ]
        )


class TestLogging:
    def create_file(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test_foo(subtests):
                logging.info("before")

                with subtests.test("sub1"):
                    print("sub1 stdout")
                    logging.info("sub1 logging")

                with subtests.test("sub2"):
                    print("sub2 stdout")
                    logging.info("sub2 logging")
                    assert False
            """
        )

    def test_capturing(self, pytester: pytest.Pytester) -> None:
        self.create_file(pytester)
        result = pytester.runpytest("--log-level=INFO")
        result.stdout.fnmatch_lines(
            [
                "*___ test_foo [[]sub2[]] __*",
                "*-- Captured stdout call --*",
                "sub2 stdout",
                "*-- Captured log call ---*",
                "INFO     root:test_capturing.py:12 sub2 logging",
                "*== short test summary info ==*",
            ]
        )

    def test_caplog(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test(subtests, caplog):
                caplog.set_level(logging.INFO)
                logging.info("start test")

                with subtests.test("sub1"):
                    logging.info("inside %s", "subtest1")

                assert len(caplog.records) == 2
                assert caplog.records[0].getMessage() == "start test"
                assert caplog.records[1].getMessage() == "inside subtest1"
            """
        )
        result = pytester.runpytest()
        result.stdout.fnmatch_lines(
            [
                "*1 passed*",
            ]
        )

    def test_no_logging(self, pytester: pytest.Pytester) -> None:
        pytester.makepyfile(
            """
            import logging

            def test(subtests):
                logging.info("start log line")

                with subtests.test("sub passing"):
                    logging.info("inside %s", "passing log line")

                with subtests.test("sub failing"):
                    logging.info("inside %s", "failing log line")
                    assert False

                logging.info("end log line")
            """
        )
        result = pytester.runpytest("-p no:logging")
        result.stdout.fnmatch_lines(
            [
                "*1 passed*",
            ]
        )
        result.stdout.no_fnmatch_line("*root:test_no_logging.py*log line*")


class TestDebugging:
    """Check --pdb support for subtests fixture and TestCase.subTest."""

    class _FakePdb:
        """
        Fake debugger class implementation that tracks which methods were called on it.
        """

        quitting: bool = False
        calls: list[str] = []

        def __init__(self, *_: object, **__: object) -> None:
            self.calls.append("init")

        def reset(self) -> None:
            self.calls.append("reset")

        def interaction(self, *_: object) -> None:
            self.calls.append("interaction")

    @pytest.fixture(autouse=True)
    def cleanup_calls(self) -> None:
        self._FakePdb.calls.clear()

    def test_pdb_fixture(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            """
            def test(subtests):
                with subtests.test():
                    assert 0
            """
        )
        self.runpytest_and_check_pdb(pytester, monkeypatch)

    def test_pdb_unittest(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytester.makepyfile(
            """
            from unittest import TestCase
            class Test(TestCase):
                def test(self):
                    with self.subTest():
                        assert 0
            """
        )
        self.runpytest_and_check_pdb(pytester, monkeypatch)

    def runpytest_and_check_pdb(
        self, pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Install the fake pdb implementation in pytest_subtests so we can reference
        # it in the command line (any module would do).
        import pytest_subtests

        monkeypatch.setattr(pytest_subtests, "_CustomPdb", self._FakePdb, raising=False)
        result = pytester.runpytest("--pdb", "--pdbcls=pytest_subtests:_CustomPdb")

        # Ensure pytest entered in debugging mode when encountering the failing
        # assert.
        result.stdout.fnmatch_lines("*entering PDB*")
        assert self._FakePdb.calls == ["init", "reset", "interaction"]
