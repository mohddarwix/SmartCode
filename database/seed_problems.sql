-- ============================================================================
-- AI Programming Tutor - PROBLEMS / CONTENT SEED
-- Safe to re-run while real users exist in the DB. Touches ONLY:
--   skills, problems, problem_skills, test_cases, hint_templates, ai_solutions
-- and never deletes from `problems`/`skills` (uses INSERT ... ON DUPLICATE KEY
-- UPDATE so foreign keys from user data — submissions, problem_status, etc.
-- — keep pointing at the same rows).
-- ============================================================================

USE ai_tutor_system;

-- ---------------------------------------------------------------------------
-- SKILLS  (the six radar axes) — upsert so existing user_skill FKs stay valid
-- ---------------------------------------------------------------------------
INSERT INTO skills (skill_id, name, description, display_order) VALUES
(1, 'Algorithms',       'Algorithmic problem solving and pattern recognition', 1),
(2, 'Data Structures',  'Arrays, lists, trees, graphs, hash tables, heaps',     2),
(3, 'Edge Cases',       'Identifying and handling boundary conditions',         3),
(4, 'Code Quality',     'Readability, naming, structure, idiomatic style',      4),
(6, 'Time Complexity',  'Analyzing asymptotic behavior',                        6)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    display_order = VALUES(display_order);
-- Note: skill_id 5 ('Debugging') was removed; the gap is intentional so existing
-- foreign keys (problem_skills, user_skill) continue to point at the same skills.
DELETE FROM skills WHERE skill_id = 5;

-- ---------------------------------------------------------------------------
-- PROBLEMS  (15 LeetCode-style classics) — upsert
-- ---------------------------------------------------------------------------
INSERT INTO problems (problem_id, slug, title, difficulty, source, estimated_minutes, statement_md, constraints_md, starter_code_md) VALUES
(1, 'two-sum', 'Two Sum', 'easy', 'leetcode', 15,
 'Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`.\n\nYou may assume that each input has exactly one solution, and you may not use the same element twice. The answer may be returned in any order.',
 '- 2 <= nums.length <= 10^4\n- -10^9 <= nums[i] <= 10^9\n- -10^9 <= target <= 10^9\n- Exactly one valid answer exists.',
 'class Solution:\n    def twoSum(self, nums: list[int], target: int) -> list[int]:\n        # Write your solution here\n        pass\n'),

(2, 'valid-parentheses', 'Valid Parentheses', 'easy', 'leetcode', 15,
 'Given a string `s` containing only the characters `(`, `)`, `{`, `}`, `[`, `]`, determine whether the string is valid.\n\nA string is valid if every opening bracket is closed by the same kind of bracket, and brackets are closed in the correct order.',
 '- 1 <= s.length <= 10^4\n- s consists only of the six bracket characters.',
 'class Solution:\n    def isValid(self, s: str) -> bool:\n        # Write your solution here\n        pass\n'),

(3, 'reverse-linked-list', 'Reverse Linked List', 'easy', 'leetcode', 20,
 'Given the `head` of a singly linked list, reverse the list and return its new head.\n\nA singly linked list node has fields `val` and `next`.',
 '- The number of nodes is in the range [0, 5000].\n- -5000 <= Node.val <= 5000.',
 '# class ListNode:\n#     def __init__(self, val=0, next=None):\n#         self.val = val\n#         self.next = next\n\nclass Solution:\n    def reverseList(self, head: "ListNode | None") -> "ListNode | None":\n        # Write your solution here\n        pass\n'),

(4, 'climbing-stairs', 'Climbing Stairs', 'easy', 'leetcode', 15,
 'You are climbing a staircase. It takes `n` steps to reach the top. Each time you can climb either 1 or 2 steps. Return the number of distinct ways you can reach the top.',
 '- 1 <= n <= 45',
 'class Solution:\n    def climbStairs(self, n: int) -> int:\n        # Write your solution here\n        pass\n'),

(5, 'best-time-to-buy-and-sell-stock', 'Best Time to Buy and Sell Stock', 'easy', 'leetcode', 15,
 'You are given an array `prices` where `prices[i]` is the price of a stock on the i-th day. You may choose a single day to buy and a later day to sell. Return the maximum profit you can achieve. If no profit is possible, return 0.',
 '- 1 <= prices.length <= 10^5\n- 0 <= prices[i] <= 10^4',
 'class Solution:\n    def maxProfit(self, prices: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(6, 'maximum-subarray', 'Maximum Subarray', 'medium', 'leetcode', 25,
 'Given an integer array `nums`, find the contiguous subarray with the largest sum and return its sum.\n\nA subarray is a contiguous, non-empty sequence of elements.',
 '- 1 <= nums.length <= 10^5\n- -10^4 <= nums[i] <= 10^4',
 'class Solution:\n    def maxSubArray(self, nums: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(7, 'container-with-most-water', 'Container With Most Water', 'medium', 'leetcode', 25,
 'You are given an integer array `height` of length `n`. The i-th line has endpoints at `(i, 0)` and `(i, height[i])`. Find two lines that, together with the x-axis, form a container that holds the most water. Return the maximum amount of water the container can store.',
 '- 2 <= height.length <= 10^5\n- 0 <= height[i] <= 10^4',
 'class Solution:\n    def maxArea(self, height: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(8, 'three-sum', '3Sum', 'medium', 'leetcode', 35,
 'Given an integer array `nums`, return all triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, `j != k` and `nums[i] + nums[j] + nums[k] == 0`.\n\nThe solution set must not contain duplicate triplets.',
 '- 3 <= nums.length <= 3000\n- -10^5 <= nums[i] <= 10^5',
 'class Solution:\n    def threeSum(self, nums: list[int]) -> list[list[int]]:\n        # Write your solution here\n        pass\n'),

(9, 'group-anagrams', 'Group Anagrams', 'medium', 'leetcode', 25,
 'Given an array of strings `strs`, group the anagrams together. You can return the answer in any order.\n\nAn anagram is a word formed by rearranging the letters of another word, using all the original letters exactly once.',
 '- 1 <= strs.length <= 10^4\n- 0 <= strs[i].length <= 100\n- strs[i] consists of lowercase English letters.',
 'class Solution:\n    def groupAnagrams(self, strs: list[str]) -> list[list[str]]:\n        # Write your solution here\n        pass\n'),

(10, 'number-of-islands', 'Number of Islands', 'medium', 'leetcode', 35,
 'Given an `m x n` 2D binary grid which represents a map of `1`s (land) and `0`s (water), return the number of islands.\n\nAn island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically. You may assume all four edges of the grid are surrounded by water.',
 '- 1 <= m, n <= 300\n- grid[i][j] is "0" or "1".',
 'class Solution:\n    def numIslands(self, grid: list[list[str]]) -> int:\n        # Write your solution here\n        pass\n'),

(11, 'coin-change', 'Coin Change', 'medium', 'leetcode', 35,
 'You are given an integer array `coins` representing coin denominations and an integer `amount`. Return the fewest number of coins needed to make up that amount. If it cannot be made up by any combination of the coins, return -1.\n\nYou may assume an infinite supply of each coin.',
 '- 1 <= coins.length <= 12\n- 1 <= coins[i] <= 2^31 - 1\n- 0 <= amount <= 10^4',
 'class Solution:\n    def coinChange(self, coins: list[int], amount: int) -> int:\n        # Write your solution here\n        pass\n'),

(12, 'longest-substring-without-repeating-characters', 'Longest Substring Without Repeating Characters', 'medium', 'leetcode', 30,
 'Given a string `s`, find the length of the longest substring without repeating characters.',
 '- 0 <= s.length <= 5 * 10^4\n- s consists of English letters, digits, symbols and spaces.',
 'class Solution:\n    def lengthOfLongestSubstring(self, s: str) -> int:\n        # Write your solution here\n        pass\n'),

(13, 'trapping-rain-water', 'Trapping Rain Water', 'hard', 'leetcode', 45,
 'Given an array `height` representing an elevation map where each bar has width 1, compute how much water can be trapped after raining.',
 '- 1 <= height.length <= 2 * 10^4\n- 0 <= height[i] <= 10^5',
 'class Solution:\n    def trap(self, height: list[int]) -> int:\n        # Write your solution here\n        pass\n'),

(14, 'word-ladder', 'Word Ladder', 'hard', 'leetcode', 50,
 'Given two words `beginWord` and `endWord`, and a dictionary `wordList`, return the number of words in the shortest transformation sequence from `beginWord` to `endWord` such that each adjacent pair of words differs by a single letter, and every intermediate word exists in `wordList`. Return 0 if no such sequence exists.',
 '- 1 <= beginWord.length <= 10\n- endWord.length == beginWord.length\n- 1 <= wordList.length <= 5000\n- All words consist of lowercase English letters.',
 'class Solution:\n    def ladderLength(self, beginWord: str, endWord: str, wordList: list[str]) -> int:\n        # Write your solution here\n        pass\n'),

(15, 'median-of-two-sorted-arrays', 'Median of Two Sorted Arrays', 'hard', 'leetcode', 50,
 'Given two sorted arrays `nums1` and `nums2` of sizes `m` and `n` respectively, return the median of the two sorted arrays. The overall run time complexity should be O(log (m+n)).',
 '- nums1.length == m\n- nums2.length == n\n- 0 <= m, n <= 1000\n- 1 <= m + n <= 2000\n- -10^6 <= nums1[i], nums2[i] <= 10^6',
 'class Solution:\n    def findMedianSortedArrays(self, nums1: list[int], nums2: list[int]) -> float:\n        # Write your solution here\n        pass\n')
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
-- PROBLEM_SKILLS  (junction table — nothing in user data references it by PK)
-- ---------------------------------------------------------------------------
DELETE FROM problem_skills WHERE problem_id BETWEEN 1 AND 15;
INSERT INTO problem_skills (problem_id, skill_id, weight) VALUES
(1, 1, 1.0), (1, 2, 1.0),                  -- Two Sum
(2, 2, 1.0), (2, 3, 0.8),                  -- Valid Parentheses
(3, 2, 1.0),                               -- Reverse Linked List (Debugging skill removed)
(4, 1, 1.0), (4, 6, 0.7),                  -- Climbing Stairs (DP)
(5, 1, 1.0), (5, 3, 0.7),                  -- Best Time to Buy/Sell Stock
(6, 1, 1.0), (6, 6, 1.0),                  -- Maximum Subarray (Kadane)
(7, 1, 1.0), (7, 3, 0.8),                  -- Container With Most Water
(8, 1, 1.0), (8, 2, 0.8), (8, 3, 0.8),     -- 3Sum
(9, 2, 1.0), (9, 4, 0.5),                  -- Group Anagrams
(10, 1, 1.0), (10, 2, 1.0),                -- Number of Islands (BFS/DFS)
(11, 1, 1.0), (11, 6, 1.0),                -- Coin Change (DP)
(12, 1, 1.0), (12, 2, 0.8),                -- Longest Substring
(13, 1, 1.0), (13, 3, 1.0),                -- Trapping Rain Water
(14, 1, 1.0), (14, 2, 1.0), (14, 6, 0.8),  -- Word Ladder (BFS)
(15, 1, 1.0), (15, 6, 1.0);                -- Median of Two Sorted Arrays

-- ---------------------------------------------------------------------------
-- TEST_CASES  (6-8 per problem: 2 visible samples + public + hidden edges)
-- ---------------------------------------------------------------------------
DELETE FROM test_cases WHERE problem_id BETWEEN 1 AND 15;
INSERT INTO test_cases (problem_id, name, visibility, input_blob, expected_blob) VALUES
-- Two Sum
(1, 'example 1',    'sample', 'nums = [2,7,11,15]\ntarget = 9',   '[0,1]'),
(1, 'example 2',    'sample', 'nums = [3,2,4]\ntarget = 6',       '[1,2]'),
(1, 'duplicates',   'public', 'nums = [3,3]\ntarget = 6',         '[0,1]'),
(1, 'negatives',    'hidden', 'nums = [-3,4,3,90]\ntarget = 0',   '[0,2]'),
(1, 'large gap',    'hidden', 'nums = [1,2,3,4,5,6,7,8,9,10]\ntarget = 19', '[8,9]'),
(1, 'two elements', 'hidden', 'nums = [5,5]\ntarget = 10',        '[0,1]'),
(1, 'zero target',  'hidden', 'nums = [0,4,3,0]\ntarget = 0',     '[0,3]'),

-- Valid Parentheses
(2, 'simple',        'sample', 's = "()"',          'true'),
(2, 'mixed',         'sample', 's = "()[]{}"',      'true'),
(2, 'mismatch',      'public', 's = "(]"',          'false'),
(2, 'nested',        'public', 's = "([{}])"',      'true'),
(2, 'empty',         'hidden', 's = ""',            'true'),
(2, 'only opener',   'hidden', 's = "("',           'false'),
(2, 'only closer',   'hidden', 's = "]"',           'false'),
(2, 'wrong order',   'hidden', 's = "([)]"',        'false'),

-- Reverse Linked List
(3, 'list of 5',  'sample', 'head = [1,2,3,4,5]',  '[5,4,3,2,1]'),
(3, 'pair',       'sample', 'head = [1,2]',        '[2,1]'),
(3, 'empty',      'public', 'head = []',           '[]'),
(3, 'single',     'hidden', 'head = [42]',         '[42]'),
(3, 'negatives',  'hidden', 'head = [-1,-2,-3]',   '[-3,-2,-1]'),
(3, 'duplicates', 'hidden', 'head = [1,1,2,2]',    '[2,2,1,1]'),

-- Climbing Stairs
(4, 'n=2',  'sample', 'n = 2',  '2'),
(4, 'n=3',  'sample', 'n = 3',  '3'),
(4, 'n=1',  'public', 'n = 1',  '1'),
(4, 'n=5',  'hidden', 'n = 5',  '8'),
(4, 'n=10', 'hidden', 'n = 10', '89'),
(4, 'n=20', 'hidden', 'n = 20', '10946'),
(4, 'n=45', 'hidden', 'n = 45', '1836311903'),

-- Best Time to Buy/Sell Stock
(5, 'profit',     'sample', 'prices = [7,1,5,3,6,4]',  '5'),
(5, 'no profit',  'sample', 'prices = [7,6,4,3,1]',    '0'),
(5, 'single',     'public', 'prices = [5]',            '0'),
(5, 'two days',   'hidden', 'prices = [1,2]',          '1'),
(5, 'flat',       'hidden', 'prices = [3,3,3,3]',      '0'),
(5, 'late spike', 'hidden', 'prices = [2,4,1,7]',      '6'),
(5, 'zeros',      'hidden', 'prices = [0,0,0,0]',      '0'),

-- Maximum Subarray
(6, 'example',      'sample', 'nums = [-2,1,-3,4,-1,2,1,-5,4]', '6'),
(6, 'all negative', 'sample', 'nums = [-3,-1,-2]',              '-1'),
(6, 'single pos',   'public', 'nums = [42]',                    '42'),
(6, 'single neg',   'hidden', 'nums = [-5]',                    '-5'),
(6, 'all positive', 'hidden', 'nums = [1,2,3,4,5]',             '15'),
(6, 'mixed',        'hidden', 'nums = [5,4,-1,7,8]',            '23'),
(6, 'alternating',  'hidden', 'nums = [-1,2,-1,2,-1,2]',        '4'),

-- Container With Most Water
(7, 'example',  'sample', 'height = [1,8,6,2,5,4,8,3,7]',  '49'),
(7, 'two bars', 'sample', 'height = [1,1]',                '1'),
(7, 'flat',     'public', 'height = [4,4,4,4]',            '12'),
(7, 'spike',    'hidden', 'height = [1,2,1]',              '2'),
(7, 'ascending','hidden', 'height = [1,2,3,4,5]',          '6'),
(7, 'descending','hidden','height = [5,4,3,2,1]',          '6'),
(7, 'zeros',    'hidden', 'height = [0,2,0,2,0]',          '4'),

-- 3Sum
(8, 'example',    'sample', 'nums = [-1,0,1,2,-1,-4]', '[[-1,-1,2],[-1,0,1]]'),
(8, 'no triplet', 'sample', 'nums = [0,1,1]',          '[]'),
(8, 'all zero',   'public', 'nums = [0,0,0]',          '[[0,0,0]]'),
(8, 'four zeros', 'hidden', 'nums = [0,0,0,0]',        '[[0,0,0]]'),
(8, 'too small',  'hidden', 'nums = [1,2]',            '[]'),
(8, 'symmetric',  'hidden', 'nums = [-2,0,1,1,2]',     '[[-2,0,2],[-2,1,1]]'),
(8, 'duplicates', 'hidden', 'nums = [-1,-1,-1,2]',     '[[-1,-1,2]]'),

-- Group Anagrams
(9, 'example',   'sample', 'strs = ["eat","tea","tan","ate","nat","bat"]', '[["eat","tea","ate"],["tan","nat"],["bat"]]'),
(9, 'empty list','sample', 'strs = []',                                    '[]'),
(9, 'single',    'public', 'strs = ["a"]',                                 '[["a"]]'),
(9, 'one empty', 'hidden', 'strs = [""]',                                  '[[""]]'),
(9, 'all same',  'hidden', 'strs = ["abc","cab","bca"]',                   '[["abc","cab","bca"]]'),
(9, 'no anagrams','hidden','strs = ["abc","def","ghi"]',                   '[["abc"],["def"],["ghi"]]'),

-- Number of Islands
(10, 'example', 'sample',
 'grid = [\n  ["1","1","1","1","0"],\n  ["1","1","0","1","0"],\n  ["1","1","0","0","0"],\n  ["0","0","0","0","0"]\n]', '1'),
(10, 'three islands', 'sample',
 'grid = [\n  ["1","1","0","0","0"],\n  ["1","1","0","0","0"],\n  ["0","0","1","0","0"],\n  ["0","0","0","1","1"]\n]', '3'),
(10, 'all water',  'public', 'grid = [["0","0"],["0","0"]]',                      '0'),
(10, 'all land',   'hidden', 'grid = [["1","1"],["1","1"]]',                      '1'),
(10, 'single 1',   'hidden', 'grid = [["1"]]',                                    '1'),
(10, 'single 0',   'hidden', 'grid = [["0"]]',                                    '0'),
(10, 'diagonal',   'hidden', 'grid = [["1","0","1"],["0","1","0"],["1","0","1"]]','5'),

-- Coin Change
(11, 'classic',     'sample', 'coins = [1,2,5]\namount = 11',     '3'),
(11, 'impossible',  'sample', 'coins = [2]\namount = 3',          '-1'),
(11, 'zero',        'public', 'coins = [1]\namount = 0',          '0'),
(11, 'exact one',   'hidden', 'coins = [1,2,5]\namount = 5',      '1'),
(11, 'large amt',   'hidden', 'coins = [1,2,5]\namount = 100',    '20'),
(11, 'big coin',    'hidden', 'coins = [186,419,83,408]\namount = 6249', '20'),
(11, 'amt below',   'hidden', 'coins = [5,10]\namount = 3',       '-1'),

-- Longest Substring Without Repeating Characters
(12, 'example 1', 'sample', 's = "abcabcbb"',  '3'),
(12, 'example 2', 'sample', 's = "bbbbb"',     '1'),
(12, 'pwwkew',    'public', 's = "pwwkew"',    '3'),
(12, 'empty',     'hidden', 's = ""',          '0'),
(12, 'single',    'hidden', 's = "a"',         '1'),
(12, 'all uniq',  'hidden', 's = "abcdef"',    '6'),
(12, 'spaces',    'hidden', 's = "a b c a b"', '3'),

-- Trapping Rain Water
(13, 'example',   'sample', 'height = [0,1,0,2,1,0,1,3,2,1,2,1]', '6'),
(13, 'mountain',  'sample', 'height = [4,2,0,3,2,5]',             '9'),
(13, 'flat',      'public', 'height = [3,3,3,3]',                 '0'),
(13, 'ascending', 'hidden', 'height = [1,2,3,4,5]',               '0'),
(13, 'descending','hidden', 'height = [5,4,3,2,1]',               '0'),
(13, 'single bar','hidden', 'height = [7]',                       '0'),
(13, 'valley',    'hidden', 'height = [5,0,5]',                   '5'),

-- Word Ladder
(14, 'example', 'sample',
 'beginWord = "hit"\nendWord = "cog"\nwordList = ["hot","dot","dog","lot","log","cog"]', '5'),
(14, 'no path', 'sample',
 'beginWord = "hit"\nendWord = "cog"\nwordList = ["hot","dot","dog","lot","log"]', '0'),
(14, 'end missing', 'public',
 'beginWord = "a"\nendWord = "c"\nwordList = ["a","b","c"]', '2'),
(14, 'one step', 'hidden',
 'beginWord = "hot"\nendWord = "dog"\nwordList = ["hot","dog","dot"]', '3'),
(14, 'same start end', 'hidden',
 'beginWord = "hot"\nendWord = "hot"\nwordList = ["hot"]', '0'),
(14, 'long chain', 'hidden',
 'beginWord = "lost"\nendWord = "miss"\nwordList = ["most","mist","miss","lost","fist","fish"]', '4'),

-- Median of Two Sorted Arrays
(15, 'example 1',   'sample', 'nums1 = [1,3]\nnums2 = [2]',         '2.00000'),
(15, 'example 2',   'sample', 'nums1 = [1,2]\nnums2 = [3,4]',       '2.50000'),
(15, 'one empty',   'public', 'nums1 = []\nnums2 = [1]',            '1.00000'),
(15, 'other empty', 'hidden', 'nums1 = [2]\nnums2 = []',            '2.00000'),
(15, 'equal mid',   'hidden', 'nums1 = [1,2]\nnums2 = [1,2]',       '1.50000'),
(15, 'negatives',   'hidden', 'nums1 = [-5,3]\nnums2 = [-2,4]',     '0.50000'),
(15, 'big merge',   'hidden', 'nums1 = [1,2,3]\nnums2 = [4,5,6,7]', '4.00000');

-- ---------------------------------------------------------------------------
-- HINT_TEMPLATES  (no incoming user-data FKs)
-- ---------------------------------------------------------------------------
DELETE FROM hint_templates WHERE problem_id BETWEEN 1 AND 15;
INSERT INTO hint_templates (problem_id, hint_level, hint_text_md) VALUES
(1, 1, 'Think about what data structure lets you look up a value in O(1).'),
(1, 2, 'Iterate once. Store each number with its index in a hash map. For each `x`, check if `target - x` is already in the map.'),
(2, 1, 'Track open brackets in a stack and pop on closes.'),
(2, 2, 'On a closing bracket, the top of the stack must match its opener; otherwise return false. An empty stack at the end means a valid string.'),
(4, 1, 'How many ways to reach step n in terms of step n-1 and step n-2?'),
(4, 2, 'You only need the last two values, not the whole array.'),
(5, 1, 'Track the lowest price you have seen so far while scanning left to right.'),
(5, 2, 'At each step, the best profit ending here is `price - min_so_far`. Keep the maximum.'),
(6, 1, 'For each element, either extend the previous subarray or start a new one.'),
(6, 2, 'Maintain `current = max(num, current + num)` and `best = max(best, current)`.'),
(7, 1, 'Two pointers, one at each end.'),
(7, 2, 'Area is `min(height[l], height[r]) * (r - l)`. Move the pointer at the shorter side inward.'),
(10, 1, 'Flood-fill each unvisited "1" cell.'),
(10, 2, 'When you find a "1", DFS (or BFS) and mark every connected "1" as visited. Count one island per fresh DFS start.'),
(13, 1, 'How much water sits on top of each bar?'),
(13, 2, 'Water on bar `i` = `min(maxLeft[i], maxRight[i]) - height[i]`. Two-pointer sweep avoids the prefix arrays.'),
(14, 1, 'Model words as graph nodes; edges connect words differing by one letter. Shortest path = BFS.'),
(14, 2, 'Bidirectional BFS from both endpoints is far faster on the typical input.');

-- ---------------------------------------------------------------------------
-- AI_SOLUTIONS  (no incoming user-data FKs)
-- ---------------------------------------------------------------------------
DELETE FROM ai_solutions WHERE problem_id BETWEEN 1 AND 15;
INSERT INTO ai_solutions (problem_id, explanation_md, solution_code, time_complexity, space_complexity) VALUES
(1, 'Use a hash map. For each element `x`, check whether `target - x` has been seen before; if so, return the stored index and the current index. Otherwise store `x` with its index. One pass, no nested loops.',
 'class Solution:\n    def twoSum(self, nums, target):\n        seen = {}\n        for i, x in enumerate(nums):\n            if target - x in seen:\n                return [seen[target - x], i]\n            seen[x] = i\n',
 'O(n)', 'O(n)'),

(2, 'Scan left to right. Push every opener onto a stack; on a closer, pop the top and verify it matches. If the stack ends empty, the string is balanced.',
 'class Solution:\n    def isValid(self, s):\n        pairs = {")": "(", "]": "[", "}": "{"}\n        stack = []\n        for c in s:\n            if c in "([{":\n                stack.append(c)\n            else:\n                if not stack or stack.pop() != pairs[c]:\n                    return False\n        return not stack\n',
 'O(n)', 'O(n)'),

(6, 'Kadane''s algorithm: at each index, decide whether to extend the running subarray or restart at the current element, then keep the maximum running value seen.',
 'class Solution:\n    def maxSubArray(self, nums):\n        best = current = nums[0]\n        for x in nums[1:]:\n            current = max(x, current + x)\n            best = max(best, current)\n        return best\n',
 'O(n)', 'O(1)'),

(10, 'Iterate over the grid. Whenever you see an unvisited "1", DFS to flood-fill the whole island (mark cells as "0" or use a visited set), then increment the count.',
 'class Solution:\n    def numIslands(self, grid):\n        if not grid: return 0\n        m, n = len(grid), len(grid[0])\n        def dfs(r, c):\n            if r < 0 or c < 0 or r >= m or c >= n or grid[r][c] != "1":\n                return\n            grid[r][c] = "0"\n            dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)\n        count = 0\n        for r in range(m):\n            for c in range(n):\n                if grid[r][c] == "1":\n                    dfs(r, c); count += 1\n        return count\n',
 'O(m*n)', 'O(m*n)'),

(13, 'Two pointers from both ends. Track running `left_max` and `right_max`. Whichever side has the smaller running max, that side''s current bar caps how much water sits there, so add `running_max - height[i]` and advance.',
 'class Solution:\n    def trap(self, height):\n        l, r = 0, len(height) - 1\n        left_max = right_max = 0\n        total = 0\n        while l < r:\n            if height[l] < height[r]:\n                left_max = max(left_max, height[l])\n                total += left_max - height[l]\n                l += 1\n            else:\n                right_max = max(right_max, height[r])\n                total += right_max - height[r]\n                r -= 1\n        return total\n',
 'O(n)', 'O(1)');
