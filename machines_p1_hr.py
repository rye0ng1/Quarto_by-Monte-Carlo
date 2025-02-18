import numpy as np
import random
from itertools import product

import time
import math
import copy


class MCTSNode:
    def __init__(self, board, available_pieces, parent=None, move=None):
        self.board = board
        self.available_pieces = available_pieces
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.value = 0
        self.move_count = 0


class P2:
    def __init__(self, board, available_pieces):
        self.pieces = [(i, j, k, l) for i in range(2) for j in range(2) for k in range(2) for l in range(2)]
        self.board = board
        self.available_pieces = available_pieces
        self.simulation_count = 100  # Default : 1,000
        self.exploration_constant = 0.75

    def select_piece(self):
        root = MCTSNode(self.board, self.available_pieces)
        
        safe_pieces = []
        for piece in self.available_pieces:
            is_safe = True
            for row, col in product(range(4), repeat=2):
                if self.board[row][col] == 0:
                    temp_board = copy.deepcopy(self.board)
                    temp_board[row][col] = self.pieces.index(piece) + 1

                    if self.check_win(temp_board):
                        is_safe = False
                        break
            if is_safe:
                safe_pieces.append(piece)
        print(f"Safe pieces: {safe_pieces}")
        
        if not safe_pieces:
            print("No safe pieces available. Choosing randomly.")
            return random.choice(self.available_pieces)

        for _ in range(self.simulation_count):
            node = self.select(root, None)
            
            if node.move and node.move[0] not in safe_pieces:
                continue
            
            value = 1 - self.simulate(node)
            self.backpropagate(node, value)
            
        best_child = max(
            root.children, 
            key=lambda c: (c.visits if c.move[0] in safe_pieces else -1)
        )        
        # best_child = max(valid_children, key=lambda c: c.visits)
        # best_child = min(root.children, key=lambda c: c.value)
        return best_child.move[0]

    def place_piece(self, selected_piece):
        root = MCTSNode(self.board, self.available_pieces)
        print(selected_piece)  # test_page

        for _ in range(self.simulation_count):
            move_count = 0  # Manage all process count
            node = self.select(root, selected_piece)
            value = self.simulate(node)
            self.backpropagate(node, value)

        best_child = max(root.children, key=lambda c: c.visits)
        # print("root's value: " + str(root.value))  # test_page
        return best_child.move[1]

    def select(self, node, piece):
        if piece is None:
            piece = random.choice(self.available_pieces)

        while node.children:
            # print("children exist")  # test_pages
            '''
            # Additional child node extensions
            if not all(child.visits > 0 for child in node.children):
                print("[Message] children exist but not visits")  # test_pages
                return self.expand(node, piece)
            '''
            node = self.uct_select(node)
            print(f"select: {node}")
            return node  # test_page
            # break  # test_page

        print("[Message] no children")  # test_page
        return self.expand(node, piece)

    def expand(self, node, piece):
        if self.is_terminal(node.board):
            return node

        for row, col in product(range(4), repeat=2):
            if node.board[row][col] == 0:
                new_board = copy.deepcopy(node.board)

                new_board[row][col] = self.pieces.index(piece) + 1
                new_available_pieces = node.available_pieces[:]

                print(f"add children in row: {row} col: {col}")  # test_page
                child = MCTSNode(new_board, new_available_pieces, node, (piece, (row, col)))
                node.children.append(child)

        return self.uct_select(node)
        # return random.choice(node.children)

    def simulate(self, node):
        board = copy.deepcopy(node.board)
        available_pieces = node.available_pieces[:]
        move_count = 0

        while not self.is_terminal(board) and available_pieces:
            piece = random.choice(available_pieces)
            empty_cells = [(r, c) for r, c in product(range(4), repeat=2) if board[r][c] == 0]

            if not empty_cells:
                break

            row, col = random.choice(empty_cells)
            board[row][col] = self.pieces.index(piece) + 1
            available_pieces.remove(piece)
            move_count = move_count + 1

        return self.evaluate(move_count)

    def backpropagate(self, node, value):
        while node:
            node.visits += 1            
            node.value += value
            print(f"node's visit: {node.visits:>4}, node's value: {node.value:>4}")  # test_page
            #print(f"node's value: {node.value:>4}")  # test_page
            node = node.parent
        print("--")

    def uct_select(self, node):
        for child in node.children:
            if child.visits == 0:
                return child

        return max(node.children, key=lambda c: c.value / c.visits + 2 * self.exploration_constant * math.sqrt(
                                                math.log(node.visits) / c.visits))

    def is_terminal(self, board):
        return self.check_win(board) or all(board[r][c] != 0 for r, c in product(range(4), repeat=2))

    def check_line(self, line):
        if 0 in line:
            return False  # Incomplete line

        characteristics = np.array([self.pieces[piece_idx - 1] for piece_idx in line])

        for i in range(4):  # Check each characteristic (I/E, N/S, T/F, P/J)
            if len(set(characteristics[:, i])) == 1:  # All share the same characteristic
                return True

        return False

    def check_2x2_subgrid_win(self, board):
        for r in range(3):
            for c in range(3):
                subgrid = [board[r][c], board[r][c + 1], board[r + 1][c], board[r + 1][c + 1]]

                if 0 not in subgrid:  # All cells must be filled
                    characteristics = [self.pieces[idx - 1] for idx in subgrid]

                    for i in range(4):  # Check each characteristic (I/E, N/S, T/F, P/J)
                        if len(set(char[i] for char in characteristics)) == 1:  # All share the same characteristic
                            return True

        return False

    def check_win(self, board):
        # Check rows, columns, and diagonals
        for col in range(4):
            if self.check_line([board[row][col] for row in range(4)]):
                return True

        for row in range(4):
            if self.check_line([board[row][col] for col in range(4)]):
                return True

        if self.check_line([board[i][i] for i in range(4)]) or self.check_line([board[i][3 - i] for i in range(4)]):
            return True

        # Check 2x2 sub-grids
        if self.check_2x2_subgrid_win(board):
            return True

        return False

    def evaluate(self, count):
        if count % 2 == 0:
            return 1  # 승
        else:
            return 0  # 패
