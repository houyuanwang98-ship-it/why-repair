"""Compatibility entrypoint for the modular proof checker."""

from proof_repair.contracts import *
from proof_repair.text import *
from proof_repair.io_session import *
from proof_repair.retrieval import *
from proof_repair.calculation import *
from proof_repair.parsing import *
from proof_repair.graph import *
from proof_repair.subquestions import *
from proof_repair.diagnosis import *
from proof_repair.adjudication import *
from proof_repair.pipeline import *
from proof_repair.cli import *


if __name__ == "__main__":
    main()
