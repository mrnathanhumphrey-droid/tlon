"""Run-harness invariants: things that must be true of every measurement.

Currently one member -- `paired`, the comparison guard. It lives here rather
than in a tool because a lesson written into a verdict does not hold: the
unpaired comparison has been the project's recurring error five times, was
written up twice as a lesson, and was committed again after both.
"""
