-- ============================================================================
-- SmartCode - EXTRA PROBLEMS SEED (problems 16-55)
-- Adds 40 more LeetCode-style problems to the catalog. Safe to re-run while
-- real users exist - only touches problems/problem_skills/test_cases/hint_templates
-- for the 16..55 range and never deletes from users/submissions/etc.
-- ============================================================================

USE ai_tutor_system;

-- ---------------------------------------------------------------------------
-- PROBLEMS 16-55 (40 new) - upsert
-- ---------------------------------------------------------------------------
INSERT INTO problems (problem_id, slug, title, difficulty, source, estimated_minutes, statement_md, constraints_md, starter_code_md) VALUES

-- ==================== EASY (16-30) ====================
(16, 'contains-duplicate', 'Contains Duplicate', 'easy', 'leetcode', 10,
 'Given an integer array `nums`, return `True` if any value appears at least twice in the array, and return `False` if every element is distinct.',
 '- 1 <= nums.length <= 10^5\n- -10^9 <= nums[i] <= 10^9',
 'class Solution:\n    def containsDuplicate(self, nums: list[int]) -> bool:\n        # Write your solution here\n        pass\n'),

(17, 'valid-anagram', 'Valid Anagram', 'easy', 'leetcode', 10,
 'Given two strings `s` and `t`, return `True` if `t` is an anagram of `s`, and `False` otherwise.\n\nAn anagram is a word formed by rearranging the letters of another, using all the original letters exactly once.',
 '- 1 <= s.length, t.length <= 5 * 10^4\n- s and t consist of lowercase English letters.',
 'class Solution:\n    def isAnagram(self, s: str, t: str) -> bool:\n        # Write your solution here\n        pass\n'),

(18, 'fizz-buzz', 'Fizz Buzz', 'easy', 'leetcode', 10,
 'Given an integer `n`, return a list `answer` of length `n` where for each `i` from `1` to `n`:\n- `answer[i-1] = "FizzBuzz"` if `i` is divisible by both 3 and 5,\n- `answer[i-1] = "Fizz"` if `i` is divisible by 3,\n- `answer[i-1] = "Buzz"` if `i` is divisible by 5,\n- otherwise `answer[i-1] = str(i)`.',
 '- 1 <= n <= 10^4',
 'class Solution:\n    def fizzBuzz(self, n: int) -> list[str]:\n        # Write your solution here\n        pass\n'),

(19, 'plus-one', 'Plus One', 'easy', 'leetcode', 10,
 'You are given a large integer represented as an array `digits`, where each `digits[i]` is the i-th digit of the integer (most-significant first). The integer has no leading zeros except for the value 0 itself.\n\nIncrement the integer by one and return the resulting array of digits.',
 '- 1 <= digits.length <= 100\n- 0 <= digits[i] <= 9',
 'class Solution:\n    def plusOne(self, digits: list[int]) -> list[int]:\n        # Write your solution here\n        pass\n'),

(20, 'single-number', 'Single Number', 'easy', 'leetcode', 15,
 'Given a non-empty integer array `nums` where every element appears exactly twice except for one, find that one. Your solution should run in linear time and use only constant extra space.',
 '- 1 <= nums.length <= 3 * 10^4\n- -3 * 10^4 <= nums[i] <= 3 * 10^4\n- Each element appears twice except for one which appears once.',
 'class Solution:\n    def singleNumber(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(21, 'missing-number', 'Missing Number', 'easy', 'leetcode', 10,
 'Given an array `nums` containing `n` distinct numbers in the range `[0, n]`, return the only number in the range that is missing from the array.',
 '- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= n\n- All numbers in nums are distinct.',
 'class Solution:\n    def missingNumber(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(22, 'palindrome-number', 'Palindrome Number', 'easy', 'leetcode', 10,
 'Given an integer `x`, return `True` if `x` is a palindrome (reads the same forwards and backwards), and `False` otherwise. Negative numbers are not palindromes.',
 '- -2^31 <= x <= 2^31 - 1',
 'class Solution:\n    def isPalindrome(self, x: int) -> bool:\n        # Write your solution here\n        pass\n'),

(23, 'reverse-integer', 'Reverse Integer', 'easy', 'leetcode', 15,
 'Given a signed 32-bit integer `x`, return `x` with its digits reversed. If reversing causes the value to fall outside the signed 32-bit range `[-2^31, 2^31 - 1]`, return `0`.\n\nAssume the environment does not allow 64-bit integers and you must detect overflow yourself.',
 '- -2^31 <= x <= 2^31 - 1',
 'class Solution:\n    def reverse(self, x: int) -> int:\n        # Write your solution here\n        pass\n'),

(24, 'roman-to-integer', 'Roman to Integer', 'easy', 'leetcode', 15,
 'Given a Roman numeral `s` (uppercase characters from `I, V, X, L, C, D, M`), convert it to its integer value.\n\nIn Roman numerals, a smaller symbol placed before a larger one is subtracted (e.g., `IV = 4`, `IX = 9`); otherwise symbols are added left to right.',
 '- 1 <= s.length <= 15\n- s contains only valid Roman characters.\n- The value of s is in [1, 3999].',
 'class Solution:\n    def romanToInt(self, s: str) -> int:\n        # Write your solution here\n        pass\n'),

(25, 'majority-element', 'Majority Element', 'easy', 'leetcode', 15,
 'Given an array `nums` of size `n`, return the element that appears more than `n / 2` times. You may assume the majority element always exists.',
 '- 1 <= nums.length <= 5 * 10^4\n- -10^9 <= nums[i] <= 10^9',
 'class Solution:\n    def majorityElement(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(26, 'move-zeroes', 'Move Zeroes', 'easy', 'leetcode', 15,
 'Given an integer array `nums`, move all `0`s to the end while keeping the relative order of the non-zero elements unchanged.\n\nReturn the modified list.',
 '- 1 <= nums.length <= 10^4\n- -2^31 <= nums[i] <= 2^31 - 1',
 'class Solution:\n    def moveZeroes(self, nums: list[int]) -> list[int]:\n        # Write your solution here\n        pass\n'),

(27, 'happy-number', 'Happy Number', 'easy', 'leetcode', 15,
 'A positive integer is *happy* if repeatedly replacing it with the sum of the squares of its digits eventually reaches `1`. If the process loops forever without reaching `1`, the number is not happy.\n\nReturn `True` if `n` is a happy number.',
 '- 1 <= n <= 2^31 - 1',
 'class Solution:\n    def isHappy(self, n: int) -> bool:\n        # Write your solution here\n        pass\n'),

(28, 'power-of-two', 'Power of Two', 'easy', 'leetcode', 10,
 'Given an integer `n`, return `True` if it is a power of two (i.e., `n == 2^k` for some non-negative integer `k`), and `False` otherwise.',
 '- -2^31 <= n <= 2^31 - 1',
 'class Solution:\n    def isPowerOfTwo(self, n: int) -> bool:\n        # Write your solution here\n        pass\n'),

(29, 'excel-sheet-column-number', 'Excel Sheet Column Number', 'easy', 'leetcode', 10,
 'Given a string `columnTitle` representing a spreadsheet column title (as in Excel), return its corresponding column number.\n\nA -> 1, B -> 2, ..., Z -> 26, AA -> 27, AB -> 28, ...',
 '- 1 <= columnTitle.length <= 7\n- columnTitle consists of uppercase English letters.\n- columnTitle is a valid title in [A, FXSHRXW].',
 'class Solution:\n    def titleToNumber(self, columnTitle: str) -> int:\n        # Write your solution here\n        pass\n'),

(30, 'length-of-last-word', 'Length of Last Word', 'easy', 'leetcode', 10,
 'Given a string `s` consisting of words and spaces, return the length of the last word in the string. A word is a maximal substring of non-space characters.',
 '- 1 <= s.length <= 10^4\n- s consists of English letters and spaces.\n- There is at least one word in s.',
 'class Solution:\n    def lengthOfLastWord(self, s: str) -> int:\n        # Write your solution here\n        pass\n'),

-- ==================== MEDIUM (31-45) ====================
(31, 'product-of-array-except-self', 'Product of Array Except Self', 'medium', 'leetcode', 25,
 'Given an integer array `nums`, return an array `answer` such that `answer[i]` is the product of all elements of `nums` except `nums[i]`. The algorithm must run in `O(n)` time and must not use division.',
 '- 2 <= nums.length <= 10^5\n- -30 <= nums[i] <= 30\n- The product of any prefix or suffix fits in a 32-bit integer.',
 'class Solution:\n    def productExceptSelf(self, nums: list[int]) -> list[int]:\n        # Write your solution here\n        pass\n'),

(32, 'rotate-array', 'Rotate Array', 'medium', 'leetcode', 20,
 'Given an integer array `nums`, rotate it to the right by `k` steps, where `k` is non-negative. Return the rotated array.',
 '- 1 <= nums.length <= 10^5\n- -2^31 <= nums[i] <= 2^31 - 1\n- 0 <= k <= 10^5',
 'class Solution:\n    def rotate(self, nums: list[int], k: int) -> list[int]:\n        # Write your solution here\n        pass\n'),

(33, 'search-in-rotated-sorted-array', 'Search in Rotated Sorted Array', 'medium', 'leetcode', 30,
 'A sorted array of distinct integers `nums` was rotated at some unknown pivot, so the array might look like `[4,5,6,7,0,1,2]`. Given the rotated array and a `target` value, return the index of `target` or `-1` if it is not present.\n\nYou must write an algorithm with `O(log n)` runtime.',
 '- 1 <= nums.length <= 5000\n- -10^4 <= nums[i] <= 10^4\n- All values of nums are unique.',
 'class Solution:\n    def search(self, nums: list[int], target: int) -> int:\n        # Write your solution here\n        pass\n'),

(34, 'sort-colors', 'Sort Colors', 'medium', 'leetcode', 25,
 'Given an array `nums` with `n` objects colored red, white, or blue (represented by `0`, `1`, and `2`), sort them in place so colors appear in the order red, white, blue. Return the modified list.',
 '- 1 <= nums.length <= 300\n- nums[i] is 0, 1, or 2.',
 'class Solution:\n    def sortColors(self, nums: list[int]) -> list[int]:\n        # Write your solution here\n        pass\n'),

(35, 'rotate-image', 'Rotate Image', 'medium', 'leetcode', 30,
 'You are given an `n x n` 2D `matrix` representing an image. Rotate it by 90 degrees clockwise in place and return the modified matrix.',
 '- n == matrix.length == matrix[i].length\n- 1 <= n <= 20\n- -1000 <= matrix[i][j] <= 1000',
 'class Solution:\n    def rotate(self, matrix: list[list[int]]) -> list[list[int]]:\n        # Write your solution here\n        pass\n'),

(36, 'subsets', 'Subsets', 'medium', 'leetcode', 25,
 'Given an integer array `nums` of unique elements, return all possible subsets (the power set). The solution may be returned in any order, and the empty subset must be included.',
 '- 1 <= nums.length <= 10\n- -10 <= nums[i] <= 10\n- All elements of nums are unique.',
 'class Solution:\n    def subsets(self, nums: list[int]) -> list[list[int]]:\n        # Write your solution here\n        pass\n'),

(37, 'combination-sum', 'Combination Sum', 'medium', 'leetcode', 30,
 'Given an array of distinct integers `candidates` and a target integer `target`, return a list of all unique combinations of `candidates` whose elements sum to `target`. Each number from `candidates` may be chosen an unlimited number of times.',
 '- 1 <= candidates.length <= 30\n- 2 <= candidates[i] <= 40\n- All elements of candidates are distinct.\n- 1 <= target <= 40',
 'class Solution:\n    def combinationSum(self, candidates: list[int], target: int) -> list[list[int]]:\n        # Write your solution here\n        pass\n'),

(38, 'spiral-matrix', 'Spiral Matrix', 'medium', 'leetcode', 25,
 'Given an `m x n` matrix, return all elements of the matrix in spiral order (starting from top-left, moving right then down then left then up, and so on, peeling off the outer ring each iteration).',
 '- m == matrix.length, n == matrix[i].length\n- 1 <= m, n <= 10\n- -100 <= matrix[i][j] <= 100',
 'class Solution:\n    def spiralOrder(self, matrix: list[list[int]]) -> list[int]:\n        # Write your solution here\n        pass\n'),

(39, 'unique-paths', 'Unique Paths', 'medium', 'leetcode', 20,
 'A robot stands at the top-left corner of an `m x n` grid. It can only move right or down. How many distinct paths can it take to reach the bottom-right corner?',
 '- 1 <= m, n <= 100\n- The answer fits in a 32-bit signed integer.',
 'class Solution:\n    def uniquePaths(self, m: int, n: int) -> int:\n        # Write your solution here\n        pass\n'),

(40, 'minimum-path-sum', 'Minimum Path Sum', 'medium', 'leetcode', 25,
 'Given an `m x n` grid of non-negative integers, find a path from top-left to bottom-right that minimizes the sum of values along the path. You may only move right or down. Return that minimum sum.',
 '- m == grid.length, n == grid[i].length\n- 1 <= m, n <= 200\n- 0 <= grid[i][j] <= 200',
 'class Solution:\n    def minPathSum(self, grid: list[list[int]]) -> int:\n        # Write your solution here\n        pass\n'),

(41, 'jump-game', 'Jump Game', 'medium', 'leetcode', 25,
 'Given an integer array `nums` where each `nums[i]` is the maximum jump length from index `i`, return `True` if you can reach the last index starting from index 0, and `False` otherwise.',
 '- 1 <= nums.length <= 10^4\n- 0 <= nums[i] <= 10^5',
 'class Solution:\n    def canJump(self, nums: list[int]) -> bool:\n        # Write your solution here\n        pass\n'),

(42, 'word-break', 'Word Break', 'medium', 'leetcode', 30,
 'Given a string `s` and a list of strings `wordDict`, return `True` if `s` can be segmented into a space-separated sequence of one or more dictionary words. The same word in `wordDict` may be reused multiple times.',
 '- 1 <= s.length <= 300\n- 1 <= wordDict.length <= 1000\n- 1 <= wordDict[i].length <= 20\n- s and wordDict[i] consist of lowercase English letters.',
 'class Solution:\n    def wordBreak(self, s: str, wordDict: list[str]) -> bool:\n        # Write your solution here\n        pass\n'),

(43, 'longest-increasing-subsequence', 'Longest Increasing Subsequence', 'medium', 'leetcode', 30,
 'Given an integer array `nums`, return the length of the longest strictly increasing subsequence.',
 '- 1 <= nums.length <= 2500\n- -10^4 <= nums[i] <= 10^4',
 'class Solution:\n    def lengthOfLIS(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(44, 'house-robber', 'House Robber', 'medium', 'leetcode', 25,
 'You are a robber planning to rob a row of houses. Each house has an amount of money, but adjacent houses are connected to the same alarm, so robbing two adjacent houses triggers it. Given an integer array `nums` representing money at each house, return the maximum amount you can rob without alerting the police.',
 '- 1 <= nums.length <= 100\n- 0 <= nums[i] <= 400',
 'class Solution:\n    def rob(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(45, 'kth-largest-element-in-an-array', 'Kth Largest Element in an Array', 'medium', 'leetcode', 25,
 'Given an integer array `nums` and an integer `k`, return the k-th largest element in the array (the k-th element of the array sorted in descending order, NOT the k-th distinct value).',
 '- 1 <= k <= nums.length <= 10^5\n- -10^4 <= nums[i] <= 10^4',
 'class Solution:\n    def findKthLargest(self, nums: list[int], k: int) -> int:\n        # Write your solution here\n        pass\n'),

-- ==================== HARD (46-55) ====================
(46, 'edit-distance', 'Edit Distance', 'hard', 'leetcode', 40,
 'Given two strings `word1` and `word2`, return the minimum number of single-character edits (insertions, deletions, or substitutions) required to convert `word1` into `word2`.',
 '- 0 <= word1.length, word2.length <= 500\n- word1 and word2 consist of lowercase English letters.',
 'class Solution:\n    def minDistance(self, word1: str, word2: str) -> int:\n        # Write your solution here\n        pass\n'),

(47, 'first-missing-positive', 'First Missing Positive', 'hard', 'leetcode', 40,
 'Given an unsorted integer array `nums`, return the smallest positive integer that does not appear in it. Your algorithm must run in `O(n)` time and use only `O(1)` extra space (beyond the input array).',
 '- 1 <= nums.length <= 10^5\n- -2^31 <= nums[i] <= 2^31 - 1',
 'class Solution:\n    def firstMissingPositive(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(48, 'largest-rectangle-in-histogram', 'Largest Rectangle in Histogram', 'hard', 'leetcode', 45,
 'Given an array `heights` representing a histogram where each bar has width 1, return the area of the largest rectangle that can be formed within the histogram.',
 '- 1 <= heights.length <= 10^5\n- 0 <= heights[i] <= 10^4',
 'class Solution:\n    def largestRectangleArea(self, heights: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(49, 'n-queens-count', 'N-Queens II', 'hard', 'leetcode', 40,
 'The n-queens puzzle asks you to place `n` queens on an `n x n` chessboard so that no two queens attack each other (no two share a row, column, or diagonal). Given `n`, return the number of distinct solutions.',
 '- 1 <= n <= 9',
 'class Solution:\n    def totalNQueens(self, n: int) -> int:\n        # Write your solution here\n        pass\n'),

(50, 'sliding-window-maximum', 'Sliding Window Maximum', 'hard', 'leetcode', 40,
 'Given an integer array `nums` and an integer `k`, slide a window of size `k` from the left to the right of the array. At each position, record the maximum element inside the window. Return the list of maxima.',
 '- 1 <= nums.length <= 10^5\n- -10^4 <= nums[i] <= 10^4\n- 1 <= k <= nums.length',
 'class Solution:\n    def maxSlidingWindow(self, nums: list[int], k: int) -> list[int]:\n        # Write your solution here\n        pass\n'),

(51, 'minimum-window-substring', 'Minimum Window Substring', 'hard', 'leetcode', 50,
 'Given two strings `s` and `t`, return the minimum-length substring of `s` that contains every character of `t` (including duplicates). If no such substring exists, return the empty string `""`. If multiple windows tie on length, return the one that appears first in `s`.',
 '- m == s.length, n == t.length\n- 1 <= m, n <= 10^5\n- s and t consist of uppercase and lowercase English letters.',
 'class Solution:\n    def minWindow(self, s: str, t: str) -> str:\n        # Write your solution here\n        pass\n'),

(52, 'burst-balloons', 'Burst Balloons', 'hard', 'leetcode', 45,
 'You are given `n` balloons indexed from `0` to `n-1`, each painted with a number on it represented by the array `nums`. You may pop the balloons in any order. When you pop balloon `i`, you earn `nums[left] * nums[i] * nums[right]` coins (where `left` and `right` are the indices of the adjacent unpopped balloons, treating out-of-bounds as `1`). Return the maximum total coins.',
 '- n == nums.length\n- 1 <= n <= 300\n- 0 <= nums[i] <= 100',
 'class Solution:\n    def maxCoins(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(53, 'wildcard-matching', 'Wildcard Matching', 'hard', 'leetcode', 40,
 'Given an input string `s` and a pattern `p`, implement wildcard matching with support for `?` (matches any single character) and `*` (matches any sequence of characters, including the empty sequence). The match must cover the **entire** input string (not partial).',
 '- 0 <= s.length, p.length <= 2000\n- s contains only lowercase English letters.\n- p contains lowercase English letters, ? and *.',
 'class Solution:\n    def isMatch(self, s: str, p: str) -> bool:\n        # Write your solution here\n        pass\n'),

(54, 'regular-expression-matching', 'Regular Expression Matching', 'hard', 'leetcode', 45,
 'Implement regular-expression matching with support for `.` (matches any single character) and `*` (matches zero or more of the preceding element). The match must cover the **entire** input string.',
 '- 1 <= s.length <= 20\n- 1 <= p.length <= 20\n- s contains only lowercase English letters.\n- p contains only lowercase English letters, . and *.',
 'class Solution:\n    def isMatch(self, s: str, p: str) -> bool:\n        # Write your solution here\n        pass\n'),

(55, 'longest-valid-parentheses', 'Longest Valid Parentheses', 'hard', 'leetcode', 40,
 'Given a string containing just the characters `(` and `)`, return the length of the longest valid (well-formed) parentheses substring.',
 '- 0 <= s.length <= 3 * 10^4\n- s[i] is "(" or ")".',
 'class Solution:\n    def longestValidParentheses(self, s: str) -> int:\n        # Write your solution here\n        pass\n')

ON DUPLICATE KEY UPDATE
    slug = VALUES(slug),
    title = VALUES(title),
    difficulty = VALUES(difficulty),
    source = VALUES(source),
    estimated_minutes = VALUES(estimated_minutes),
    statement_md = VALUES(statement_md),
    constraints_md = VALUES(constraints_md),
    starter_code_md = VALUES(starter_code_md);

-- ---------------------------------------------------------------------------
-- PROBLEM_SKILLS (junction table, IDs 16-55)
-- ---------------------------------------------------------------------------
DELETE FROM problem_skills WHERE problem_id BETWEEN 16 AND 55;
INSERT INTO problem_skills (problem_id, skill_id, weight) VALUES
-- Easy
(16, 2, 1.0),                              -- Contains Duplicate -> Data Structures
(17, 2, 1.0),                              -- Valid Anagram -> Data Structures
(18, 1, 0.6), (18, 4, 0.8),                -- Fizz Buzz -> Algorithms (light), Code Quality
(19, 1, 1.0), (19, 3, 1.0),                -- Plus One -> Algorithms, Edge Cases (carry)
(20, 1, 1.0), (20, 6, 0.6),                -- Single Number -> Algorithms, Time Complexity (XOR)
(21, 1, 1.0), (21, 3, 0.7),                -- Missing Number -> Algorithms, Edge Cases
(22, 1, 0.8), (22, 3, 1.0),                -- Palindrome Number -> Algorithms, Edge Cases (negatives)
(23, 1, 0.8), (23, 3, 1.0),                -- Reverse Integer -> Algorithms, Edge Cases (overflow)
(24, 1, 1.0), (24, 2, 0.6),                -- Roman to Integer
(25, 1, 1.0), (25, 2, 0.6),                -- Majority Element (Boyer-Moore)
(26, 1, 1.0), (26, 2, 0.8),                -- Move Zeroes -> Algorithms, Arrays
(27, 1, 1.0), (27, 2, 0.7),                -- Happy Number -> Algorithms, Cycle Detection
(28, 1, 0.8), (28, 6, 0.7),                -- Power of Two -> Algorithms, Time Complexity (bit)
(29, 1, 1.0),                              -- Excel Sheet Column Number -> Algorithms
(30, 1, 0.6), (30, 3, 1.0),                -- Length of Last Word -> Edge Cases (trailing spaces)
-- Medium
(31, 1, 1.0), (31, 6, 1.0),                -- Product Except Self
(32, 1, 1.0), (32, 2, 0.7),                -- Rotate Array
(33, 1, 1.0), (33, 6, 1.0),                -- Search in Rotated Sorted Array
(34, 1, 1.0), (34, 2, 0.8),                -- Sort Colors (Dutch flag)
(35, 1, 1.0), (35, 2, 0.8),                -- Rotate Image
(36, 1, 1.0), (36, 2, 0.7),                -- Subsets (backtracking)
(37, 1, 1.0), (37, 2, 0.7),                -- Combination Sum
(38, 1, 1.0), (38, 2, 0.8),                -- Spiral Matrix
(39, 1, 1.0), (39, 6, 0.8),                -- Unique Paths (DP)
(40, 1, 1.0), (40, 6, 0.8),                -- Minimum Path Sum (DP)
(41, 1, 1.0), (41, 6, 0.7),                -- Jump Game (greedy)
(42, 1, 1.0), (42, 6, 0.8),                -- Word Break (DP)
(43, 1, 1.0), (43, 6, 1.0),                -- LIS
(44, 1, 1.0), (44, 6, 0.8),                -- House Robber
(45, 1, 1.0), (45, 2, 1.0), (45, 6, 0.8),  -- Kth Largest (heap/quickselect)
-- Hard
(46, 1, 1.0), (46, 6, 1.0),                -- Edit Distance
(47, 1, 1.0), (47, 3, 1.0), (47, 6, 1.0),  -- First Missing Positive
(48, 1, 1.0), (48, 2, 1.0), (48, 6, 0.8),  -- Largest Rectangle (mono stack)
(49, 1, 1.0), (49, 2, 0.7),                -- N-Queens
(50, 1, 1.0), (50, 2, 1.0), (50, 6, 1.0),  -- Sliding Window Max (deque)
(51, 1, 1.0), (51, 2, 1.0), (51, 3, 0.8),  -- Min Window Substring
(52, 1, 1.0), (52, 6, 1.0),                -- Burst Balloons (interval DP)
(53, 1, 1.0), (53, 6, 0.8),                -- Wildcard Matching
(54, 1, 1.0), (54, 6, 0.8),                -- Regex Matching
(55, 1, 1.0), (55, 2, 0.8), (55, 3, 1.0);  -- Longest Valid Parentheses

-- ---------------------------------------------------------------------------
-- TEST_CASES for IDs 16-55 (6 per problem average)
-- ---------------------------------------------------------------------------
DELETE FROM test_cases WHERE problem_id BETWEEN 16 AND 55;
INSERT INTO test_cases (problem_id, name, visibility, input_blob, expected_blob) VALUES
-- ==================== EASY ====================
-- Contains Duplicate
(16, 'has dup',     'sample', 'nums = [1,2,3,1]',                'true'),
(16, 'no dup',      'sample', 'nums = [1,2,3,4]',                'false'),
(16, 'mixed dup',   'public', 'nums = [1,1,1,3,3,4,3,2,4,2]',    'true'),
(16, 'single',      'hidden', 'nums = [1]',                      'false'),
(16, 'two same',    'hidden', 'nums = [-1,-1]',                  'true'),
(16, 'negatives',   'hidden', 'nums = [-1,-2,-3,-4]',            'false'),

-- Valid Anagram
(17, 'anagram',    'sample', 's = "anagram"\nt = "nagaram"', 'true'),
(17, 'not anagram','sample', 's = "rat"\nt = "car"',         'false'),
(17, 'diff length','public', 's = "a"\nt = "ab"',            'false'),
(17, 'same',       'hidden', 's = "ab"\nt = "ba"',           'true'),
(17, 'same chars diff count', 'hidden', 's = "aacc"\nt = "ccac"', 'false'),
(17, 'longer',     'hidden', 's = "listen"\nt = "silent"',   'true'),

-- Fizz Buzz
(18, 'n=3',  'sample', 'n = 3',  '["1","2","Fizz"]'),
(18, 'n=5',  'sample', 'n = 5',  '["1","2","Fizz","4","Buzz"]'),
(18, 'n=15', 'public', 'n = 15', '["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz"]'),
(18, 'n=1',  'hidden', 'n = 1',  '["1"]'),
(18, 'n=2',  'hidden', 'n = 2',  '["1","2"]'),
(18, 'n=16', 'hidden', 'n = 16', '["1","2","Fizz","4","Buzz","Fizz","7","8","Fizz","Buzz","11","Fizz","13","14","FizzBuzz","16"]'),

-- Plus One
(19, 'simple',      'sample', 'digits = [1,2,3]',     '[1,2,4]'),
(19, 'four digits', 'sample', 'digits = [4,3,2,1]',   '[4,3,2,2]'),
(19, 'rollover',    'public', 'digits = [9]',         '[1,0]'),
(19, 'all nines',   'hidden', 'digits = [9,9,9]',     '[1,0,0,0]'),
(19, 'zero',        'hidden', 'digits = [0]',         '[1]'),
(19, 'one carry',   'hidden', 'digits = [1,9]',       '[2,0]'),

-- Single Number
(20, 'three',     'sample', 'nums = [2,2,1]',      '1'),
(20, 'five',      'sample', 'nums = [4,1,2,1,2]',  '4'),
(20, 'just one',  'public', 'nums = [7]',          '7'),
(20, 'negatives', 'hidden', 'nums = [-3,5,-3,7,7]','5'),
(20, 'zero pair', 'hidden', 'nums = [0,0,1]',      '1'),
(20, 'big',       'hidden', 'nums = [4,1,2,1,2,4,9]','9'),

-- Missing Number
(21, 'three of 0..3', 'sample', 'nums = [3,0,1]',    '2'),
(21, 'two of 0..2',   'sample', 'nums = [0,1]',      '2'),
(21, 'nine of 0..9',  'public', 'nums = [9,6,4,2,3,5,7,0,1]', '8'),
(21, 'one elem',      'hidden', 'nums = [0]',        '1'),
(21, 'missing 0',     'hidden', 'nums = [1]',        '0'),
(21, 'in middle',     'hidden', 'nums = [0,1,3]',    '2'),

-- Palindrome Number
(22, 'classic',  'sample', 'x = 121',   'true'),
(22, 'negative', 'sample', 'x = -121',  'false'),
(22, 'tens',     'public', 'x = 10',    'false'),
(22, 'zero',     'hidden', 'x = 0',     'true'),
(22, 'four dig', 'hidden', 'x = 1221',  'true'),
(22, 'five dig', 'hidden', 'x = 12321', 'true'),

-- Reverse Integer
(23, 'three pos',  'sample', 'x = 123',         '321'),
(23, 'three neg',  'sample', 'x = -123',        '-321'),
(23, 'trailing 0', 'public', 'x = 120',         '21'),
(23, 'zero',       'hidden', 'x = 0',           '0'),
(23, 'overflow',   'hidden', 'x = 1534236469',  '0'),
(23, 'near max',   'hidden', 'x = 1463847412',  '2147483641'),

-- Roman to Integer
(24, 'three',    'sample', 's = "III"',       '3'),
(24, 'fiftyeight','sample','s = "LVIII"',     '58'),
(24, 'large',    'public', 's = "MCMXCIV"',   '1994'),
(24, 'four',     'hidden', 's = "IV"',        '4'),
(24, 'nine',     'hidden', 's = "IX"',        '9'),
(24, 'forty',    'hidden', 's = "XL"',        '40'),
(24, 'three M',  'hidden', 's = "MMM"',       '3000'),

-- Majority Element
(25, 'simple',    'sample', 'nums = [3,2,3]',          '3'),
(25, 'mixed',     'sample', 'nums = [2,2,1,1,1,2,2]',  '2'),
(25, 'single',    'public', 'nums = [1]',              '1'),
(25, 'four fours','hidden', 'nums = [4,4,4,4,5,5,5]',  '4'),
(25, 'all same',  'hidden', 'nums = [7,7,7,7]',        '7'),
(25, 'negative',  'hidden', 'nums = [-1,-1,1]',        '-1'),

-- Move Zeroes
(26, 'classic',    'sample', 'nums = [0,1,0,3,12]',     '[1,3,12,0,0]'),
(26, 'one zero',   'sample', 'nums = [0]',              '[0]'),
(26, 'no zeros',   'public', 'nums = [1,2,3]',          '[1,2,3]'),
(26, 'all zeros',  'hidden', 'nums = [0,0,0]',          '[0,0,0]'),
(26, 'scattered',  'hidden', 'nums = [4,0,0,5,0,6]',    '[4,5,6,0,0,0]'),
(26, 'leading 0',  'hidden', 'nums = [0,1,2,3,0,4]',    '[1,2,3,4,0,0]'),

-- Happy Number
(27, 'happy 19',     'sample', 'n = 19',  'true'),
(27, 'unhappy 2',    'sample', 'n = 2',   'false'),
(27, 'happy 7',      'public', 'n = 7',   'true'),
(27, 'one',          'hidden', 'n = 1',   'true'),
(27, 'cycle four',   'hidden', 'n = 4',   'false'),
(27, 'happy 100',    'hidden', 'n = 100', 'true'),

-- Power of Two
(28, 'one',     'sample', 'n = 1',     'true'),
(28, 'sixteen', 'sample', 'n = 16',    'true'),
(28, 'three',   'public', 'n = 3',     'false'),
(28, 'zero',    'hidden', 'n = 0',     'false'),
(28, 'negative','hidden', 'n = -8',    'false'),
(28, 'big',     'hidden', 'n = 1024',  'true'),

-- Excel Sheet Column Number
(29, 'A',  'sample', 'columnTitle = "A"',   '1'),
(29, 'AB', 'sample', 'columnTitle = "AB"',  '28'),
(29, 'ZY', 'public', 'columnTitle = "ZY"',  '701'),
(29, 'Z',  'hidden', 'columnTitle = "Z"',   '26'),
(29, 'AA', 'hidden', 'columnTitle = "AA"',  '27'),
(29, 'ZZ', 'hidden', 'columnTitle = "ZZ"',  '702'),

-- Length of Last Word
(30, 'hello world',  'sample', 's = "Hello World"',                   '5'),
(30, 'extra spaces', 'sample', 's = "   fly me   to   the moon  "',   '4'),
(30, 'sentence',     'public', 's = "luffy is still joyboy"',         '6'),
(30, 'one char',     'hidden', 's = "a"',                             '1'),
(30, 'trailing',     'hidden', 's = "trailing spaces   "',            '8'),
(30, 'two words',    'hidden', 's = "good day"',                      '3'),

-- ==================== MEDIUM ====================
-- Product of Array Except Self
(31, 'four',       'sample', 'nums = [1,2,3,4]',          '[24,12,8,6]'),
(31, 'with zero',  'sample', 'nums = [-1,1,0,-3,3]',      '[0,0,9,0,0]'),
(31, 'pair',       'public', 'nums = [2,3]',              '[3,2]'),
(31, 'ones',       'hidden', 'nums = [1,1]',              '[1,1]'),
(31, 'two zeros',  'hidden', 'nums = [0,0]',              '[0,0]'),
(31, 'small',      'hidden', 'nums = [2,3,4]',            '[12,8,6]'),

-- Rotate Array
(32, 'k=3',     'sample', 'nums = [1,2,3,4,5,6,7]\nk = 3', '[5,6,7,1,2,3,4]'),
(32, 'k=2 neg', 'sample', 'nums = [-1,-100,3,99]\nk = 2', '[3,99,-1,-100]'),
(32, 'k>n',     'public', 'nums = [1,2]\nk = 3',           '[2,1]'),
(32, 'k=0',     'hidden', 'nums = [1,2,3]\nk = 0',         '[1,2,3]'),
(32, 'single',  'hidden', 'nums = [1]\nk = 0',             '[1]'),
(32, 'big k',   'hidden', 'nums = [1,2,3,4]\nk = 6',       '[3,4,1,2]'),

-- Search in Rotated Sorted Array
(33, 'find',     'sample', 'nums = [4,5,6,7,0,1,2]\ntarget = 0',  '4'),
(33, 'absent',   'sample', 'nums = [4,5,6,7,0,1,2]\ntarget = 3',  '-1'),
(33, 'one miss', 'public', 'nums = [1]\ntarget = 0',               '-1'),
(33, 'one hit',  'hidden', 'nums = [1]\ntarget = 1',               '0'),
(33, 'pair end', 'hidden', 'nums = [1,3]\ntarget = 3',             '1'),
(33, 'rotated2', 'hidden', 'nums = [3,1]\ntarget = 1',             '1'),

-- Sort Colors
(34, 'classic',   'sample', 'nums = [2,0,2,1,1,0]', '[0,0,1,1,2,2]'),
(34, 'one each',  'sample', 'nums = [2,0,1]',       '[0,1,2]'),
(34, 'single',    'public', 'nums = [0]',           '[0]'),
(34, 'shuffled',  'hidden', 'nums = [1,2,0]',       '[0,1,2]'),
(34, 'all twos',  'hidden', 'nums = [2,2,2]',       '[2,2,2]'),
(34, 'all zeros', 'hidden', 'nums = [0,0,0]',       '[0,0,0]'),

-- Rotate Image
(35, 'three',  'sample',
 'matrix = [[1,2,3],[4,5,6],[7,8,9]]',
 '[[7,4,1],[8,5,2],[9,6,3]]'),
(35, 'four', 'sample',
 'matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]',
 '[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]'),
(35, 'one',    'public', 'matrix = [[1]]',               '[[1]]'),
(35, 'two',    'hidden', 'matrix = [[1,2],[3,4]]',       '[[3,1],[4,2]]'),
(35, 'zeros',  'hidden', 'matrix = [[0,0],[0,0]]',       '[[0,0],[0,0]]'),
(35, 'neg',    'hidden', 'matrix = [[-1,2],[3,-4]]',     '[[3,-1],[-4,2]]'),

-- Subsets
(36, 'three',  'sample', 'nums = [1,2,3]', '[[],[1],[2],[3],[1,2],[1,3],[2,3],[1,2,3]]'),
(36, 'one',    'sample', 'nums = [0]',     '[[],[0]]'),
(36, 'two',    'public', 'nums = [1,2]',   '[[],[1],[2],[1,2]]'),
(36, 'reverse','hidden', 'nums = [3,2,1]', '[[],[1],[2],[3],[1,2],[1,3],[2,3],[1,2,3]]'),
(36, 'pair',   'hidden', 'nums = [5,7]',   '[[],[5],[7],[5,7]]'),

-- Combination Sum
(37, 'classic',   'sample', 'candidates = [2,3,6,7]\ntarget = 7',  '[[2,2,3],[7]]'),
(37, 'multi',     'sample', 'candidates = [2,3,5]\ntarget = 8',    '[[2,2,2,2],[2,3,3],[3,5]]'),
(37, 'no answer', 'public', 'candidates = [2]\ntarget = 1',        '[]'),
(37, 'one cand',  'hidden', 'candidates = [1]\ntarget = 2',        '[[1,1]]'),
(37, 'exact',     'hidden', 'candidates = [1]\ntarget = 1',        '[[1]]'),
(37, 'two combo', 'hidden', 'candidates = [3,5,8]\ntarget = 11',   '[[3,3,5],[3,8]]'),

-- Spiral Matrix
(38, 'three sq', 'sample',
 'matrix = [[1,2,3],[4,5,6],[7,8,9]]',
 '[1,2,3,6,9,8,7,4,5]'),
(38, '3x4',     'sample',
 'matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]',
 '[1,2,3,4,8,12,11,10,9,5,6,7]'),
(38, 'single',  'public', 'matrix = [[1]]',               '[1]'),
(38, '2x2',     'hidden', 'matrix = [[1,2],[3,4]]',       '[1,2,4,3]'),
(38, 'column',  'hidden', 'matrix = [[1],[2],[3]]',       '[1,2,3]'),
(38, 'row',     'hidden', 'matrix = [[1,2,3]]',           '[1,2,3]'),

-- Unique Paths
(39, 'classic', 'sample', 'm = 3\nn = 7', '28'),
(39, 'small',   'sample', 'm = 3\nn = 2', '3'),
(39, 'swapped', 'public', 'm = 7\nn = 3', '28'),
(39, 'one',     'hidden', 'm = 1\nn = 1', '1'),
(39, '2x2',     'hidden', 'm = 2\nn = 2', '2'),
(39, '5x5',     'hidden', 'm = 5\nn = 5', '70'),

-- Minimum Path Sum
(40, 'classic',    'sample', 'grid = [[1,3,1],[1,5,1],[4,2,1]]', '7'),
(40, 'wide',       'sample', 'grid = [[1,2,3],[4,5,6]]',         '12'),
(40, 'one',        'public', 'grid = [[1]]',                     '1'),
(40, 'tiny',       'hidden', 'grid = [[1,2],[1,1]]',             '3'),
(40, 'big single', 'hidden', 'grid = [[7]]',                     '7'),
(40, '2x2',        'hidden', 'grid = [[1,2],[3,4]]',             '7'),

-- Jump Game
(41, 'reachable',    'sample', 'nums = [2,3,1,1,4]',  'true'),
(41, 'blocked',      'sample', 'nums = [3,2,1,0,4]',  'false'),
(41, 'single',       'public', 'nums = [0]',          'true'),
(41, 'two okay',     'hidden', 'nums = [2,0]',        'true'),
(41, 'small block',  'hidden', 'nums = [1,0,1]',      'false'),
(41, 'easy',         'hidden', 'nums = [1,2,3]',      'true'),

-- Word Break
(42, 'leetcode',    'sample', 's = "leetcode"\nwordDict = ["leet","code"]',                    'true'),
(42, 'apple pen',   'sample', 's = "applepenapple"\nwordDict = ["apple","pen"]',                'true'),
(42, 'unsegment',   'public', 's = "catsandog"\nwordDict = ["cats","dog","sand","and","cat"]', 'false'),
(42, 'reuse short', 'hidden', 's = "aaaaaaa"\nwordDict = ["aaaa","aaa"]',                       'true'),
(42, 'single chars','hidden', 's = "abc"\nwordDict = ["a","b","c"]',                            'true'),
(42, 'too short',   'hidden', 's = "abc"\nwordDict = ["ab"]',                                   'false'),

-- Longest Increasing Subsequence
(43, 'classic',      'sample', 'nums = [10,9,2,5,3,7,101,18]', '4'),
(43, 'two LIS',      'sample', 'nums = [0,1,0,3,2,3]',         '4'),
(43, 'flat',         'public', 'nums = [7,7,7,7,7,7,7]',       '1'),
(43, 'single',       'hidden', 'nums = [1]',                   '1'),
(43, 'mixed',        'hidden', 'nums = [4,10,4,3,8,9]',        '3'),
(43, 'long ascend',  'hidden', 'nums = [1,2,3,4,5,6,7]',       '7'),

-- House Robber
(44, 'small',      'sample', 'nums = [1,2,3,1]',  '4'),
(44, 'medium',     'sample', 'nums = [2,7,9,3,1]','12'),
(44, 'edges',      'public', 'nums = [2,1,1,2]',  '4'),
(44, 'single',     'hidden', 'nums = [5]',        '5'),
(44, 'two',        'hidden', 'nums = [5,1]',      '5'),
(44, 'zero',       'hidden', 'nums = [0]',        '0'),
(44, 'long',       'hidden', 'nums = [2,1,4,5,3,1,1,3]', '12'),

-- Kth Largest
(45, 'classic',  'sample', 'nums = [3,2,1,5,6,4]\nk = 2',         '5'),
(45, 'with dup', 'sample', 'nums = [3,2,3,1,2,4,5,5,6]\nk = 4',   '4'),
(45, 'one',      'public', 'nums = [1]\nk = 1',                   '1'),
(45, 'k=1',      'hidden', 'nums = [1,2]\nk = 1',                 '2'),
(45, 'k=n',      'hidden', 'nums = [1,2]\nk = 2',                 '1'),
(45, 'all same', 'hidden', 'nums = [7,7,7]\nk = 1',               '7'),
(45, 'with neg', 'hidden', 'nums = [-1,2,0]\nk = 2',              '0'),

-- ==================== HARD ====================
-- Edit Distance
(46, 'horse-ros',     'sample', 'word1 = "horse"\nword2 = "ros"',          '3'),
(46, 'long',          'sample', 'word1 = "intention"\nword2 = "execution"','5'),
(46, 'both empty',    'public', 'word1 = ""\nword2 = ""',                  '0'),
(46, 'one empty',     'hidden', 'word1 = "a"\nword2 = ""',                 '1'),
(46, 'other empty',   'hidden', 'word1 = ""\nword2 = "abc"',               '3'),
(46, 'same',          'hidden', 'word1 = "abc"\nword2 = "abc"',            '0'),

-- First Missing Positive
(47, 'classic',     'sample', 'nums = [1,2,0]',         '3'),
(47, 'with neg',    'sample', 'nums = [3,4,-1,1]',      '2'),
(47, 'all above',   'public', 'nums = [7,8,9,11,12]',   '1'),
(47, 'single 1',    'hidden', 'nums = [1]',             '2'),
(47, 'no 1',        'hidden', 'nums = [2]',             '1'),
(47, 'consecutive', 'hidden', 'nums = [1,2,3,4,5]',     '6'),

-- Largest Rectangle in Histogram
(48, 'classic',  'sample', 'heights = [2,1,5,6,2,3]', '10'),
(48, 'two bars', 'sample', 'heights = [2,4]',         '4'),
(48, 'single',   'public', 'heights = [1]',           '1'),
(48, 'zero',     'hidden', 'heights = [0]',           '0'),
(48, 'flat',     'hidden', 'heights = [2,2,2]',       '6'),
(48, 'ascending','hidden', 'heights = [1,2,3,4,5]',   '9'),
(48, 'descend',  'hidden', 'heights = [5,4,1,2]',     '8'),

-- N-Queens II
(49, 'four',  'sample', 'n = 4', '2'),
(49, 'one',   'sample', 'n = 1', '1'),
(49, 'two',   'public', 'n = 2', '0'),
(49, 'three', 'hidden', 'n = 3', '0'),
(49, 'five',  'hidden', 'n = 5', '10'),
(49, 'six',   'hidden', 'n = 6', '4'),
(49, 'eight', 'hidden', 'n = 8', '92'),

-- Sliding Window Maximum
(50, 'classic',  'sample', 'nums = [1,3,-1,-3,5,3,6,7]\nk = 3', '[3,3,5,5,6,7]'),
(50, 'k=1',      'sample', 'nums = [1]\nk = 1',                  '[1]'),
(50, 'k=1 two',  'public', 'nums = [1,-1]\nk = 1',               '[1,-1]'),
(50, 'whole',    'hidden', 'nums = [9,11]\nk = 2',               '[11]'),
(50, 'pair',     'hidden', 'nums = [4,-2]\nk = 2',               '[4]'),
(50, 'k=2 three','hidden', 'nums = [7,2,4]\nk = 2',              '[7,4]'),

-- Minimum Window Substring
(51, 'classic',    'sample', 's = "ADOBECODEBANC"\nt = "ABC"', '"BANC"'),
(51, 'single',     'sample', 's = "a"\nt = "a"',               '"a"'),
(51, 'impossible', 'public', 's = "a"\nt = "aa"',              '""'),
(51, 'two',        'hidden', 's = "ab"\nt = "b"',              '"b"'),
(51, 'one',        'hidden', 's = "ab"\nt = "a"',              '"a"'),
(51, 'same',       'hidden', 's = "abc"\nt = "abc"',           '"abc"'),

-- Burst Balloons
(52, 'classic', 'sample', 'nums = [3,1,5,8]', '167'),
(52, 'pair',    'sample', 'nums = [1,5]',     '10'),
(52, 'single',  'public', 'nums = [5]',       '5'),
(52, 'one one', 'hidden', 'nums = [1]',       '1'),
(52, 'three',   'hidden', 'nums = [1,2,3]',   '12'),
(52, 'two',     'hidden', 'nums = [4,2]',     '12'),

-- Wildcard Matching
(53, 'no match',   'sample', 's = "aa"\np = "a"',         'false'),
(53, 'star',       'sample', 's = "aa"\np = "*"',         'true'),
(53, 'q wrong',    'public', 's = "cb"\np = "?a"',        'false'),
(53, 'star middle','hidden', 's = "adceb"\np = "*a*b"',   'true'),
(53, 'cant match', 'hidden', 's = "acdcb"\np = "a*c?b"',  'false'),
(53, 'empty s',    'hidden', 's = ""\np = "*"',           'true'),
(53, 'both empty', 'hidden', 's = ""\np = ""',            'true'),
(53, 'no p',       'hidden', 's = "a"\np = ""',           'false'),

-- Regular Expression Matching
(54, 'no match',   'sample', 's = "aa"\np = "a"',           'false'),
(54, 'a star',     'sample', 's = "aa"\np = "a*"',          'true'),
(54, 'dot star',   'public', 's = "ab"\np = ".*"',          'true'),
(54, 'c star',     'hidden', 's = "aab"\np = "c*a*b"',      'true'),
(54, 'partial',    'hidden', 's = "mississippi"\np = "mis*is*p*."', 'false'),
(54, 'opt last',   'hidden', 's = "a"\np = "ab*"',          'true'),
(54, 'literal',    'hidden', 's = "abc"\np = "abc"',        'true'),

-- Longest Valid Parentheses
(55, 'open extra', 'sample', 's = "(()"',     '2'),
(55, 'close extra','sample', 's = ")()())"',  '4'),
(55, 'empty',      'public', 's = ""',        '0'),
(55, 'simple',     'hidden', 's = "()"',      '2'),
(55, 'middle',     'hidden', 's = "()(()"',   '2'),
(55, 'nested',     'hidden', 's = "()(())"',  '6'),
(55, 'long open',  'hidden', 's = "(()(((()"','2');

-- ---------------------------------------------------------------------------
-- HINT_TEMPLATES (selected coverage - 2 levels for problems likely to need help)
-- ---------------------------------------------------------------------------
DELETE FROM hint_templates WHERE problem_id BETWEEN 16 AND 55;
INSERT INTO hint_templates (problem_id, hint_level, hint_text_md) VALUES
(16, 1, 'A hash set gives O(1) membership lookup.'),
(16, 2, 'Iterate once. If you see an element you have stored before, return True; otherwise add it and continue.'),
(17, 1, 'Two strings are anagrams iff their character counts match.'),
(17, 2, 'Use a length-26 array (or `collections.Counter`) to count letters in each string and compare.'),
(18, 1, 'Check divisibility by 15 BEFORE 3 and 5 separately.'),
(19, 1, 'Walk from the last digit, adding the carry.'),
(19, 2, 'If every digit was 9, you need to prepend a new leading 1.'),
(20, 1, 'XOR has two properties: a^a = 0 and a^0 = a. Combine them.'),
(20, 2, 'XOR-fold the array. Pairs cancel out, leaving the unique value.'),
(21, 1, 'Sum 0..n minus sum of nums.'),
(21, 2, 'Or XOR every index in 0..n with every value; only the missing one is left.'),
(22, 1, 'Negatives can never be palindromes.'),
(22, 2, 'You can reverse the second half of the number numerically (no string conversion needed).'),
(23, 1, 'Build the reversed value digit by digit using `% 10` and `// 10`.'),
(23, 2, 'After each push, check if the running result exceeded `2**31 - 1` and return 0 if it would overflow.'),
(24, 1, 'Map each Roman char to its value, then sum left to right.'),
(24, 2, 'When the current symbol is smaller than the next one, subtract it instead of adding.'),
(25, 1, 'Boyer-Moore voting: maintain a candidate and a count.'),
(25, 2, 'When count hits 0, switch the candidate to the current element. Increment if the element matches, decrement otherwise. The final candidate is the majority.'),
(26, 1, 'Two pointers: read-pointer scans, write-pointer points to the next non-zero slot.'),
(26, 2, 'Walk read from 0 to n-1. When `nums[read] != 0`, swap with `nums[write]` and advance write.'),
(27, 1, 'You either reach 1 or you enter a cycle. Use a set or Floyd''s tortoise-and-hare.'),
(28, 1, 'Powers of two have exactly one bit set: `n & (n - 1) == 0`. Also exclude `n <= 0`.'),
(29, 1, 'Treat the title as a base-26 number, with A = 1 (not 0).'),
(30, 1, 'Walk from the end of the string, skipping trailing spaces, then count letters until you hit a space or the start.'),
(31, 1, 'Two passes: prefix products from the left, then suffix products from the right.'),
(31, 2, 'Allocate an output array, fill it with left-products, then multiply each by the running right-product.'),
(32, 1, 'Rotating right by k is equivalent to reversing the whole array, then reversing the first k and the last n-k.'),
(32, 2, 'Always normalize `k = k % n` first to avoid wasted work.'),
(33, 1, 'Modified binary search. At each step, one half of the array is sorted.'),
(33, 2, 'Compare `nums[mid]` to `nums[left]` to decide which half is sorted, then check whether the target lies in that half.'),
(34, 1, 'Dutch-flag three-pointer: low/mid/high.'),
(34, 2, 'Swap `nums[mid]` toward `low` if it is 0, toward `high` if it is 2; advance accordingly.'),
(35, 1, 'Transpose the matrix, then reverse each row.'),
(35, 2, 'Equivalently, swap `matrix[i][j]` with `matrix[n-1-j][i]` over the four corners of each ring.'),
(36, 1, 'For each element, choose to include it or not. Backtrack or iterate the 2^n bitmask.'),
(36, 2, 'Bitmask version: for `mask` in `0..2^n - 1`, the subset is `[nums[i] for i in range(n) if mask & (1<<i)]`.'),
(37, 1, 'Backtrack. Stay on the same candidate (it can be reused) before moving to the next.'),
(37, 2, 'Sort candidates first. Recurse with `(remaining, start_index)`. Prune when `remaining < candidate`.'),
(38, 1, 'Track four bounds (top, bottom, left, right). Peel off layers.'),
(38, 2, 'After traversing a side, shrink the corresponding bound and check if it crossed the opposite bound.'),
(39, 1, 'Pure DP: `dp[i][j] = dp[i-1][j] + dp[i][j-1]`.'),
(39, 2, 'You only need one row of size `n`; update it left to right in place.'),
(40, 1, 'DP with `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`.'),
(41, 1, 'Greedy: track the furthest reachable index as you walk.'),
(41, 2, 'If you reach an index beyond your current `max_reach`, you cannot proceed.'),
(42, 1, '`dp[i]` = can the prefix `s[:i]` be segmented?'),
(42, 2, 'For each split point j < i, if `dp[j]` is True and `s[j:i]` is in the dictionary, set `dp[i] = True`.'),
(43, 1, 'O(n^2) DP: for each i, `dp[i]` = 1 + max(`dp[j]` for j < i where `nums[j] < nums[i]`).'),
(43, 2, 'O(n log n): patience sorting. Maintain a `tails` array and binary-search each new element.'),
(44, 1, '`dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.'),
(44, 2, 'You only need the last two values, not the whole array.'),
(45, 1, 'Sorting is O(n log n). A min-heap of size k is O(n log k). Quickselect is O(n) average.'),
(45, 2, 'Min-heap approach: push every value; if size > k, pop. The root is the answer.'),
(46, 1, '`dp[i][j]` = edit distance between `word1[:i]` and `word2[:j]`.'),
(46, 2, 'Transition: if last chars match, `dp[i][j] = dp[i-1][j-1]`. Otherwise 1 + min(insert, delete, replace).'),
(47, 1, 'The answer is in `[1, n+1]` where `n = len(nums)`. Anything outside doesn''t matter.'),
(47, 2, 'Index-marking: place each value `v` in slot `v-1` (1-indexed). Then scan for the first slot whose value isn''t `i+1`.'),
(48, 1, 'For each bar, find the largest rectangle whose height equals that bar.'),
(48, 2, 'Use a monotonic increasing stack of bar indices. Pop until you find a smaller bar; each pop computes a rectangle.'),
(49, 1, 'Place queens row by row, tracking three sets: columns, two diagonals.'),
(49, 2, 'Two diagonals are tracked as `row + col` and `row - col` per queen. Backtrack on conflict.'),
(50, 1, 'A monotonic deque of indices solves this in O(n).'),
(50, 2, 'Push new index to the back, popping smaller values first. Pop from the front when the leftmost index leaves the window.'),
(51, 1, 'Sliding window. Expand right until valid, then shrink from the left while still valid.'),
(51, 2, 'Track required char counts. Maintain a `formed` counter; the window is valid iff `formed == required`.'),
(52, 1, 'Reverse perspective: think of bursting balloon `k` LAST in the range `(i, j)`.'),
(52, 2, 'Interval DP: `dp[i][j] = max over k of dp[i][k] + dp[k][j] + nums[i] * nums[k] * nums[j]`. Pad with 1s at both ends.'),
(53, 1, '`dp[i][j]` = does `p[:j]` match `s[:i]`?'),
(53, 2, 'When `p[j-1] == "*"`: `dp[i][j] = dp[i][j-1]` (zero match) OR `dp[i-1][j]` (one more char absorbed).'),
(54, 1, '`dp[i][j]` again, but `*` now repeats the preceding char.'),
(54, 2, 'When `p[j-1] == "*"`: try ZERO repetitions (`dp[i][j-2]`) OR (if last char matches) one more (`dp[i-1][j]`).'),
(55, 1, 'A counter doesn''t work alone — track positions with a stack.'),
(55, 2, 'Push the index of every "(". On ")", pop; if the stack is now empty, push the current index as a new base. Otherwise the length is `i - stack.top()`.');

-- ---------------------------------------------------------------------------
-- AI_SOLUTIONS (left empty -- the live-streaming solver generates these
-- on demand; pre-baking 40 canonical solutions isn't required for the UX)
-- ---------------------------------------------------------------------------
DELETE FROM ai_solutions WHERE problem_id BETWEEN 16 AND 55;
