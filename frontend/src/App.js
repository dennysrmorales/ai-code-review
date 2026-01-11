import React, { useState } from 'react';
import * as Sentry from '@sentry/react';
import CodeEditor from './components/CodeEditor';
import ReviewResults from './components/ReviewResults';
import './App.css';

function App() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleReview = async () => {
    if (!code.trim()) {
      setError('Please enter some code to review');
      return;
    }

    setLoading(true);
    setError(null);
    setReviewData(null);

    try {
      const response = await fetch('http://localhost:8000/api/review/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, language }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to review code');
      }

      setReviewData(data.review);
    } catch (err) {
      setError(err.message);
      console.error('Review error:', err);
      Sentry.captureException(err, {
        tags: {
          component: 'CodeReview',
          action: 'handleReview',
        },
        extra: {
          language,
          codeLength: code.length,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI-Powered Code Review Assistant</h1>
        <p>Analyze your code for issues, inefficiencies, and bugs</p>
      </header>
      <main className="App-main">
        <div className="editor-section">
          <div className="editor-header">
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)}
              className="language-select"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
              <option value="c">C</option>
              <option value="typescript">TypeScript</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
            </select>
            <button 
              onClick={handleReview} 
              disabled={loading}
              className="review-button"
            >
              {loading ? 'Analyzing...' : 'Review Code'}
            </button>
          </div>
          <CodeEditor 
            value={code} 
            onChange={setCode}
            language={language}
          />
          {error && <div className="error-message">{error}</div>}
        </div>
        <div className="results-section">
          <ReviewResults 
            reviewData={reviewData}
            code={code}
            loading={loading}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
