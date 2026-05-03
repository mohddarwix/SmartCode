import React, { useState } from 'react';
import { BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Code, BookOpen, TrendingUp, Award, ChevronRight, Play, CheckCircle, AlertCircle, Lightbulb, Send, Menu, User, LogOut } from 'lucide-react';

const AIProgrammingTutor = () => {
  const [currentScreen, setCurrentScreen] = useState('login');
  const [selectedField, setSelectedField] = useState('Problem Solving');
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [showHint, setShowHint] = useState(false);
  const [code, setCode] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [diagnosticAnswers, setDiagnosticAnswers] = useState({});
  const [diagnosticStarted, setDiagnosticStarted] = useState(false);
  const [dashboardTab, setDashboardTab] = useState('skills');

  // Mock data
  const diagnosticQuestions = [
    {
      id: 'mcq1',
      type: 'mcq',
      skill: 'Algorithms',
      question: 'What is the time complexity of binary search?',
      options: ['O(n)', 'O(log n)', 'O(n log n)', 'O(n²)'],
      correct: 1,
      explanation: 'Binary search eliminates half of the remaining elements with each iteration, resulting in O(log n) complexity.'
    },
    {
      id: 'mcq2',
      type: 'mcq',
      skill: 'Data Structures',
      question: 'Which data structure is best for implementing a LIFO (Last In First Out) operation?',
      options: ['Queue', 'Stack', 'Linked List', 'Hash Table'],
      correct: 1,
      explanation: 'A Stack is designed specifically for LIFO operations with push (insert) and pop (remove) operations.'
    },
    {
      id: 'mcq3',
      type: 'mcq',
      skill: 'Edge Cases',
      question: 'When working with arrays, which is NOT typically an edge case?',
      options: ['Empty array', 'Single element', 'Negative numbers', 'Array with duplicates'],
      correct: 3,
      explanation: 'While important to handle, duplicate elements are not necessarily edge cases. Empty arrays, single elements, and extreme values are more critical edge cases.'
    },
    {
      id: 'mcq4',
      type: 'mcq',
      skill: 'Time Complexity',
      question: 'What is the worst-case time complexity of quicksort?',
      options: ['O(n)', 'O(n log n)', 'O(n²)', 'O(log n)'],
      correct: 2,
      explanation: 'Quicksort has O(n²) worst-case complexity when the pivot is always the smallest or largest element.'
    },
    {
      id: 'mcq5',
      type: 'mcq',
      skill: 'Code Quality',
      question: 'Which practice best improves code readability?',
      options: ['Using single-letter variable names', 'Writing longer functions', 'Adding meaningful comments', 'Avoiding function decomposition'],
      correct: 2,
      explanation: 'Meaningful comments and clear variable names significantly improve code readability and maintainability.'
    },
    {
      id: 'mcq6',
      type: 'mcq',
      skill: 'Debugging',
      question: 'What is the first step in debugging?',
      options: ['Change random code', 'Reproduce the issue', 'Read the error message', 'Add console.log everywhere'],
      correct: 1,
      explanation: 'Reproducing the issue is crucial to understand under what conditions the bug occurs.'
    },
    {
      id: 'code1',
      type: 'coding',
      skill: 'Algorithms',
      question: 'Write a function that checks if a string is a palindrome (reads the same forwards and backwards).',
      placeholder: 'function isPalindrome(str) {\n  // Your code here\n}',
      expected: 'Should return true for "racecar" and false for "hello"',
      difficulty: 'Easy'
    },
    {
      id: 'code2',
      type: 'coding',
      skill: 'Edge Cases',
      question: 'Write a function to find the maximum element in an array. Handle edge cases properly.',
      placeholder: 'function findMax(arr) {\n  // Consider: empty array, single element, negative numbers\n}',
      expected: 'Should handle null/empty arrays gracefully',
      difficulty: 'Easy'
    }
  ];
  
  const fields = [
    { id: 'basic', name: 'Basic Level', items: ['Problem Solving (Coding)', 'SQL', 'OOP'] },
    { id: 'intermediate', name: 'Intermediate Level', items: ['Clean Code', 'Design Patterns', 'Low-Level Design'] },
    { id: 'senior', name: 'Senior Level', items: ['System Design'] }
  ];

  const skillsData = [
    { skill: 'Algorithms', score: 75, fullMark: 100 },
    { skill: 'Data Structures', score: 65, fullMark: 100 },
    { skill: 'Edge Cases', score: 45, fullMark: 100 },
    { skill: 'Code Quality', score: 85, fullMark: 100 },
    { skill: 'Debugging', score: 70, fullMark: 100 },
    { skill: 'Time Complexity', score: 50, fullMark: 100 }
  ];

  const skillProgress = [
    { week: 'Week 1', score: 30 },
    { week: 'Week 2', score: 35 },
    { week: 'Week 3', score: 38 },
    { week: 'Week 4', score: 45 },
    { week: 'Current', score: 45 }
  ];

  const solvedProblems = [
    { id: 1, title: 'Two Sum Problem', difficulty: 'Easy', score: 85, skills: ['Algorithms', 'Data Structures'] },
    { id: 2, title: 'Binary Search Tree', difficulty: 'Medium', score: 72, skills: ['Data Structures', 'Debugging'] },
    { id: 3, title: 'Graph Traversal', difficulty: 'Hard', score: 68, skills: ['Algorithms', 'Edge Cases'] }
  ];

  // Login Screen
  const LoginScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-full mb-4">
            <Code className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800">AI Programming Tutor</h1>
          <p className="text-gray-600 mt-2">Master programming skills with personalized guidance</p>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <input type="email" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="your@email.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
            <input type="password" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent" placeholder="••••••••" />
          </div>
          <button onClick={() => setCurrentScreen('diagnostic')} className="w-full bg-indigo-600 text-white py-3 rounded-lg font-semibold hover:bg-indigo-700 transition">
            Sign In
          </button>
          <button onClick={() => setCurrentScreen('diagnostic')} className="w-full bg-white text-indigo-600 py-3 rounded-lg font-semibold border-2 border-indigo-600 hover:bg-indigo-50 transition">
            Create Account
          </button>
        </div>
      </div>
    </div>
  );

  // Diagnostic Exam Screen
  const DiagnosticScreen = () => {
    if (!diagnosticStarted) {
      return (
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Code className="w-8 h-8 text-indigo-600" />
                <span className="text-xl font-bold text-gray-800">AI Tutor</span>
              </div>
              <span className="text-gray-600 font-medium">{selectedField}</span>
            </div>
          </nav>

          <div className="max-w-4xl mx-auto p-8">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-indigo-100 rounded-full mb-4">
                  <BookOpen className="w-10 h-10 text-indigo-600" />
                </div>
                <h1 className="text-3xl font-bold text-gray-800 mb-3">Diagnostic Assessment</h1>
                <p className="text-gray-600">This initial assessment helps us understand your current skill level and create a personalized learning path.</p>
              </div>

              <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 mb-6">
                <h3 className="font-semibold text-indigo-900 mb-2">What to expect:</h3>
                <ul className="text-indigo-800 space-y-1 text-sm">
                  <li>• 6 multiple choice questions covering all skills</li>
                  <li>• 2 small coding problems to test practical skills</li>
                  <li>• Estimated time: 20-30 minutes</li>
                  <li>• Your performance will be analyzed to create your skill profile</li>
                </ul>
              </div>

              <button onClick={() => setDiagnosticStarted(true)} className="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-indigo-700 transition flex items-center justify-center space-x-2">
                <Play className="w-6 h-6" />
                <span>Start Diagnostic Exam</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    const handleMCQAnswer = (questionId, optionIndex) => {
      setDiagnosticAnswers({
        ...diagnosticAnswers,
        [questionId]: optionIndex
      });
    };

    const handleCodeAnswer = (questionId, code) => {
      setDiagnosticAnswers({
        ...diagnosticAnswers,
        [questionId]: code
      });
    };

    const handleSubmitDiagnostic = () => {
      // Navigate to dashboard after completing diagnostic
      setDiagnosticStarted(false);
      setCurrentScreen('dashboard');
    };

    return (
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Code className="w-8 h-8 text-indigo-600" />
              <span className="text-xl font-bold text-gray-800">AI Tutor</span>
            </div>
            <span className="text-gray-600 font-medium">{selectedField}</span>
          </div>
        </nav>

        <div className="max-w-4xl mx-auto p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-8">Diagnostic Test</h1>

          {/* MCQ Questions */}
          {diagnosticQuestions.filter(q => q.type === 'mcq').map((question, idx) => (
            <div key={question.id} className="bg-white rounded-xl shadow-md p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-800">{idx + 1}. {question.question}</h3>
                <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-medium">{question.skill}</span>
              </div>
              
              <div className="space-y-3">
                {question.options.map((option, optIdx) => (
                  <button
                    key={optIdx}
                    onClick={() => handleMCQAnswer(question.id, optIdx)}
                    className={`w-full text-left p-4 rounded-lg border-2 transition ${
                      diagnosticAnswers[question.id] === optIdx
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 bg-white hover:border-indigo-300'
                    }`}
                  >
                    <div className="flex items-center">
                      <div className={`w-5 h-5 rounded-full border-2 mr-3 flex items-center justify-center ${
                        diagnosticAnswers[question.id] === optIdx
                          ? 'border-indigo-600 bg-indigo-600'
                          : 'border-gray-300'
                      }`}>
                        {diagnosticAnswers[question.id] === optIdx && (
                          <CheckCircle className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <span className="text-gray-700">{option}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}

          {/* Coding Questions */}
          {diagnosticQuestions.filter(q => q.type === 'coding').map((question, idx) => (
            <div key={question.id} className="bg-white rounded-xl shadow-md p-6 mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-bold text-gray-800 mb-2">{diagnosticQuestions.filter(q => q.type === 'mcq').length + idx + 1}. {question.question}</h3>
                  <p className="text-sm text-gray-600">{question.expected}</p>
                </div>
                <div className="flex gap-2">
                  <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-medium">{question.skill}</span>
                  <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-xs font-medium">{question.difficulty}</span>
                </div>
              </div>
              
              <textarea
                value={diagnosticAnswers[question.id] || ''}
                onChange={(e) => handleCodeAnswer(question.id, e.target.value)}
                placeholder={question.placeholder}
                className="w-full h-40 p-4 bg-gray-900 text-green-400 font-mono text-sm rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>
          ))}

          <button
            onClick={handleSubmitDiagnostic}
            className="w-full bg-indigo-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-indigo-700 transition flex items-center justify-center space-x-2"
          >
            <Send className="w-6 h-6" />
            <span>Complete Diagnostic</span>
          </button>
        </div>
      </div>
    );
  };

  // Dashboard Screen
  const DashboardScreen = () => (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-800">AI Tutor</span>
          </div>
          <div className="flex items-center space-x-6">
            <span className="text-gray-600 font-medium">{selectedField || 'Problem Solving'}</span>
            <User className="w-6 h-6 text-gray-600" />
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setDashboardTab('skills')}
            className={`px-6 py-3 font-medium transition ${
              dashboardTab === 'skills'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <TrendingUp className="w-5 h-5 inline mr-2" />
            Skills & Progress
          </button>
          <button
            onClick={() => setDashboardTab('problems')}
            className={`px-6 py-3 font-medium transition ${
              dashboardTab === 'problems'
                ? 'text-indigo-600 border-b-2 border-indigo-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <Award className="w-5 h-5 inline mr-2" />
            Solved Problems
          </button>
        </div>

        {/* Skills Tab */}
        {dashboardTab === 'skills' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Sidebar - Skills List */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-md p-4">
                <h2 className="text-lg font-bold text-gray-800 mb-3">Your Skills</h2>
                <div className="space-y-2">
                  {skillsData.map((skill, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedSkill(skill.skill)}
                      className={`p-2 rounded-lg cursor-pointer transition ${
                        selectedSkill === skill.skill ? 'bg-indigo-50 border-2 border-indigo-300' : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-700 text-sm">{skill.skill}</span>
                        <span className="text-xs font-bold text-indigo-600">{skill.score}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-indigo-600 h-1.5 rounded-full transition-all"
                          style={{ width: `${skill.score}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Radar Chart */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Skills Overview</h2>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={skillsData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="skill" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar name="Your Skills" dataKey="score" stroke="#4f46e5" fill="#4f46e5" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              {/* Skill Progress Chart (shown when skill is selected) */}
              {selectedSkill && (
                <div className="bg-white rounded-xl shadow-md p-6">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">Progress: {selectedSkill}</h2>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={skillProgress}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Line type="monotone" dataKey="score" stroke="#4f46e5" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Problems Tab */}
        {dashboardTab === 'problems' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-6">Solved Problems ({solvedProblems.length})</h2>
              <div className="space-y-4">
                {solvedProblems.map((problem) => (
                  <div key={problem.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800 text-sm mb-2">{problem.title}</h3>
                        <div className="flex items-center space-x-2 text-xs text-gray-600">
                          <span className={`px-2 py-0.5 rounded ${
                            problem.difficulty === 'Easy' ? 'bg-green-100 text-green-700' :
                            problem.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {problem.difficulty}
                          </span>
                          <span className="line-clamp-1">{problem.skills.join(', ')}</span>
                        </div>
                      </div>
                      <span className="text-lg font-bold text-green-600 ml-2">{problem.score}%</span>
                    </div>
                    
                    <div className="flex gap-2">
                      <button className="flex-1 bg-indigo-50 text-indigo-600 px-3 py-2 rounded-lg font-medium hover:bg-indigo-100 transition flex items-center justify-center space-x-1 text-xs">
                        <Code className="w-4 h-4" />
                        <span>View</span>
                      </button>
                      <button className="flex-1 bg-purple-50 text-purple-600 px-3 py-2 rounded-lg font-medium hover:bg-purple-100 transition flex items-center justify-center space-x-1 text-xs">
                        <Play className="w-4 h-4" />
                        <span>Watch</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Start Next Recommendation */}
              <div className="mt-8 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold mb-1">Continue Your Learning</h3>
                    <p className="opacity-90">Ready for the next challenge?</p>
                  </div>
                  <button onClick={() => setCurrentScreen('editor')} className="bg-white text-indigo-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition flex items-center space-x-2 whitespace-nowrap">
                    <ChevronRight className="w-5 h-5" />
                    <span>Start Recommendation</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // Editor Screen
  const EditorScreen = () => (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-800">AI Tutor</span>
          </div>
          <button onClick={() => setCurrentScreen('dashboard')} className="text-gray-600 hover:text-gray-800">
            ← Back to Dashboard
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Problem Description */}
          <div className="bg-white rounded-xl shadow-md p-6 h-fit">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold text-gray-800">Balanced Binary Search Tree</h1>
              <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-medium">Medium</span>
            </div>
            
            <div className="prose max-w-none">
              <p className="text-gray-700 mb-4">
                Given a sorted array of integers, construct a balanced binary search tree. The tree should have minimal height while maintaining the BST property.
              </p>
              
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Example:</h3>
              <div className="bg-gray-50 p-3 rounded-lg mb-4 font-mono text-sm">
                Input: [-10, -3, 0, 5, 9]<br/>
                Output: A balanced BST with root 0
              </div>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">Constraints:</h3>
              <ul className="text-gray-700 text-sm space-y-1">
                <li>1 ≤ array.length ≤ 10,000</li>
                <li>Array is sorted in ascending order</li>
                <li>All values are unique</li>
              </ul>
            </div>

            <div className="mt-6 bg-indigo-50 border-l-4 border-indigo-600 p-4">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-indigo-600 mr-2 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-indigo-900">Why this problem?</h4>
                  <p className="text-sm text-indigo-800 mt-1">
                    This problem targets your weaker areas: <strong>Edge Cases</strong> and <strong>Data Structures</strong>. It will help you improve handling boundary conditions and tree construction.
                  </p>
                </div>
              </div>
            </div>

            {showHint && (
              <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-600 p-4">
                <div className="flex items-start">
                  <Lightbulb className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-yellow-900">Hint</h4>
                    <p className="text-sm text-yellow-800 mt-1">
                      Consider using the middle element as the root to ensure balance. Recursively apply this to the left and right subarrays.
                    </p>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={() => setShowHint(!showHint)}
              className="mt-4 text-indigo-600 hover:text-indigo-700 font-medium flex items-center space-x-1"
            >
              <Lightbulb className="w-4 h-4" />
              <span>{showHint ? 'Hide Hint' : 'Request Hint'}</span>
            </button>
          </div>

          {/* Code Editor */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-xl font-bold text-gray-800 mb-4">Code Editor</h2>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="// Write your solution here..."
              className="w-full h-96 p-4 bg-gray-900 text-green-400 font-mono text-sm rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
            
            <div className="mt-4 flex space-x-3">
              <button className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition">
                Run Tests
              </button>
              <button
                onClick={() => {
                  setSubmitted(true);
                  setCurrentScreen('feedback');
                }}
                className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition flex items-center justify-center space-x-2"
              >
                <Send className="w-5 h-5" />
                <span>Submit Solution</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Feedback Screen
  const FeedbackScreen = () => (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Code className="w-8 h-8 text-indigo-600" />
            <span className="text-xl font-bold text-gray-800">AI Tutor</span>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-8">
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">Great Work!</h1>
            <p className="text-xl text-gray-600">Your Score: <span className="font-bold text-indigo-600">85/100</span></p>
          </div>

          {/* Performance Breakdown */}
          <div className="bg-gray-50 rounded-lg p-6 mb-6">
            <h3 className="font-bold text-gray-800 mb-4">Performance Breakdown</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Correctness</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{width: '90%'}}></div>
                  </div>
                  <span className="text-sm font-bold text-gray-700">90%</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Edge Case Handling</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-yellow-600 h-2 rounded-full" style={{width: '70%'}}></div>
                  </div>
                  <span className="text-sm font-bold text-gray-700">70%</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Code Quality</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{width: '95%'}}></div>
                  </div>
                  <span className="text-sm font-bold text-gray-700">95%</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Time Complexity</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{width: '85%'}}></div>
                  </div>
                  <span className="text-sm font-bold text-gray-700">85%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Feedback */}
          <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
            <h3 className="font-semibold text-blue-900 mb-2">Detailed Feedback</h3>
            <ul className="text-blue-800 space-y-2 text-sm">
              <li>✓ Excellent use of recursive approach for tree construction</li>
              <li>✓ Good code readability and structure</li>
              <li>⚠ Consider adding null checks for edge case: empty array</li>
              <li>⚠ Your solution could handle single-element arrays more efficiently</li>
            </ul>
          </div>

          {/* Skills Updated */}
          <div className="bg-green-50 border-l-4 border-green-600 p-4 mb-6">
            <h3 className="font-semibold text-green-900 mb-2">Skills Updated</h3>
            <div className="text-green-800 text-sm space-y-1">
              <p>• Data Structures: 65% → 68% (+3%)</p>
              <p>• Edge Case Handling: 45% → 48% (+3%)</p>
            </div>
          </div>

          {/* Why This Problem */}
          <div className="bg-indigo-50 border-l-4 border-indigo-600 p-4 mb-6">
            <h3 className="font-semibold text-indigo-900 mb-2">Why This Problem Was Chosen</h3>
            <p className="text-indigo-800 text-sm">
              This problem was selected because your <strong>Edge Case Handling</strong> (45%) and <strong>Data Structures</strong> (65%) scores were lower than your other skills. By working on balanced tree construction, you practiced both identifying edge cases and implementing complex data structures, helping to balance your skill profile.
            </p>
          </div>

          {/* Next Recommendation */}
          <div className="bg-purple-50 border-l-4 border-purple-600 p-4 mb-6">
            <h3 className="font-semibold text-purple-900 mb-2">Next Recommended Problem</h3>
            <p className="text-purple-800 text-sm mb-2">
              <strong>Graph Cycle Detection</strong> - This will further strengthen your edge case handling while introducing graph algorithms.
            </p>
            <p className="text-purple-700 text-xs">Estimated difficulty: Medium | Time: 30-45 min</p>
          </div>

          <div className="flex space-x-4">
            <button onClick={() => setCurrentScreen('dashboard')} className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition">
              Back to Dashboard
            </button>
            <button onClick={() => setCurrentScreen('editor')} className="flex-1 bg-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition">
              Next Problem
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Render current screen
  return (
    <div>
      {currentScreen === 'login' && <LoginScreen />}
      {currentScreen === 'diagnostic' && <DiagnosticScreen />}
      {currentScreen === 'dashboard' && <DashboardScreen />}
      {currentScreen === 'editor' && <EditorScreen />}
      {currentScreen === 'feedback' && <FeedbackScreen />}
    </div>
  );
};

function App() {
  return <AIProgrammingTutor />;
}

export default App;