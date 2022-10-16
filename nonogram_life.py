from nonogram_solver.nonogram import Nonogram
import seagull as sg
from nonogram_solver.solver import solve
from seagull.lifeforms import Pulsar, Glider
import matplotlib.pyplot as plt

def main():
    # Initialize board
    board = sg.Board(size=(19, 60))

    # Add three Pulsar lifeforms in various locations
    board.add(Glider(), loc=(1, 1))
    #board.add(Pulsar(), loc=(1, 22))
    #board.add(Pulsar(), loc=(1, 42))

    board_strs = [''.join('#' if c else '.' for c in l) for l in board.state]
    nonogram = Nonogram()
    nonogram.init_from_solution_string(board_strs)
    success, _ = solve(nonogram)
    if success:
        print("IS SOLVABLE!")
    else:
        print("not solvable")

    # Simulate board
    sim = sg.Simulator(board)
    sim.run(sg.rules.conway_classic, iters=1000)

    sim.animate()
    plt.show()


if __name__ == '__main__':
    main()

