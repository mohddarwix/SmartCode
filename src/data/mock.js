// The diagnostic question pool lives client-side for now. Once the diagnostic
// has its own admin UI, these questions will be moved to a backend table.
//
// Design rules:
//   - Open-ended coding only (no MCQs).
//   - Every question tests MULTIPLE skills at once — that's how coding works.
//     `skill` is the primary skill (for the badge / label); `testedSkills`
//     is the full set the AI grader scores along.
//   - Specs are deliberately concise: main intent + ONE example. Edge cases
//     are NOT enumerated — the grader's hidden inputs are where the trick
//     lives. A careful student handles them; a hasty one doesn't.
//   - Plain-English / pseudocode answers are accepted: the grader gives
//     partial credit on understanding (Algorithms / Edge Cases / Time
//     Complexity) but Code Quality near zero, since no real code was written.

export const diagnosticQuestions = [
  {
    id: 'd1',
    type: 'coding',
    skill: 'Algorithms',
    testedSkills: ['Algorithms', 'Edge Cases', 'Code Quality'],
    difficulty: 'Easy',
    question:
      'Complete `second_largest(nums)` so it returns the second-largest DISTINCT value in `nums`.',
    expected: 'Example: second_largest([3, 1, 4, 1, 5]) -> 4',
    placeholder:
      'def second_largest(nums):\n    """Return the second-largest distinct value in `nums`."""\n    # Your code here\n',
  },
  {
    id: 'd2',
    type: 'coding',
    skill: 'Data Structures',
    testedSkills: ['Data Structures', 'Algorithms', 'Edge Cases', 'Code Quality'],
    difficulty: 'Easy',
    question:
      'Complete `first_unique_char(s)` so it returns the INDEX of the first non-repeating character in `s`.',
    expected: 'Example: first_unique_char("leetcode") -> 0',
    placeholder:
      'def first_unique_char(s):\n    """Return the index of the first non-repeating character in `s`."""\n    # Your code here\n',
  },
  {
    id: 'd3',
    type: 'coding',
    skill: 'Edge Cases',
    testedSkills: ['Edge Cases', 'Algorithms', 'Code Quality'],
    difficulty: 'Easy',
    question:
      'Complete `trimmed_mean(nums)` so it returns the arithmetic mean of `nums` after removing exactly one minimum and one maximum value.',
    expected: 'Example: trimmed_mean([1, 2, 3, 4, 5]) -> 3.0   # mean of [2, 3, 4]',
    placeholder:
      'def trimmed_mean(nums):\n    """Return the mean of `nums` after removing one min and one max."""\n    # Your code here\n',
  },
  {
    id: 'd4',
    type: 'coding',
    skill: 'Code Quality',
    testedSkills: ['Code Quality', 'Algorithms', 'Data Structures'],
    difficulty: 'Easy',
    question:
      'Complete `count_vowels_in_words(words)` so it returns a dict mapping each word in `words` to its vowel count (a, e, i, o, u — case-insensitive). Write it as cleanly and idiomatically as you can.',
    expected: 'Example: count_vowels_in_words(["Hello", "Sky"]) -> {"Hello": 2, "Sky": 0}',
    placeholder:
      'def count_vowels_in_words(words):\n    """Return {word: vowel_count} for each word in `words`."""\n    # Your code here\n',
  },
  {
    id: 'd5',
    type: 'coding',
    skill: 'Time Complexity',
    testedSkills: ['Time Complexity', 'Algorithms', 'Data Structures', 'Edge Cases'],
    difficulty: 'Medium',
    question:
      'Complete `has_pair_with_sum(nums, target)` so it returns True iff two DIFFERENT indices `i, j` satisfy `nums[i] + nums[j] == target`. `nums` can have up to 100,000 elements — your solution must run faster than O(n^2).',
    expected: 'Example: has_pair_with_sum([1, 2, 4, 4], 8) -> True   # uses indices 2 and 3',
    placeholder:
      'def has_pair_with_sum(nums, target):\n    """Return True iff some two distinct indices sum to `target`."""\n    # Your code here\n',
  },
];
