import React, { useMemo } from 'react';
import Editor from '@monaco-editor/react';
import './ReviewResults.css';

const ReviewResults = ({ reviewData, code, loading }) => {
  const highlightedCode = useMemo(() => {
    if (!reviewData || !reviewData.issues) return null;

    const lines = code.split('\n');
    const issueMap = {};
    
    reviewData.issues.forEach(issue => {
      const lineNum = issue.line - 1; // Convert to 0-based index
      if (!issueMap[lineNum]) {
        issueMap[lineNum] = [];
      }
      issueMap[lineNum].push(issue);
    });

    return { lines, issueMap };
  }, [reviewData, code]);

  const getMarkerColor = (severity) => {
    switch (severity) {
      case 'error':
        return '#ff4444';
      case 'warning':
        return '#ffaa00';
      case 'info':
        return '#4488ff';
      default:
        return '#888888';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '•';
    }
  };

  if (loading) {
    return (
      <div className="review-results loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Analyzing your code...</p>
        </div>
      </div>
    );
  }

  if (!reviewData) {
    return (
      <div className="review-results empty">
        <div className="empty-state">
          <h2>Code Review Results</h2>
          <p>Enter your code and click "Review Code" to see AI-powered suggestions and improvements.</p>
        </div>
      </div>
    );
  }

  const markers = reviewData.issues?.map(issue => ({
    startLineNumber: issue.line,
    startColumn: 1,
    endLineNumber: issue.line,
    endColumn: 1000,
    message: `${issue.severity.toUpperCase()}: ${issue.message}`,
    severity: issue.severity === 'error' ? 8 : issue.severity === 'warning' ? 4 : 2,
  })) || [];

  return (
    <div className="review-results">
      <div className="review-header">
        <h2>Review Results</h2>
        {reviewData.score !== undefined && (
          <div className="score-badge">
            Score: {reviewData.score}/100
          </div>
        )}
      </div>

      {reviewData.summary && (
        <div className="summary-section">
          <h3>Summary</h3>
          <p>{reviewData.summary}</p>
        </div>
      )}

      {reviewData.issues && reviewData.issues.length > 0 && (
        <div className="issues-section">
          <h3>Issues Found ({reviewData.issues.length})</h3>
          <div className="issues-list">
            {reviewData.issues.map((issue, index) => (
              <div key={index} className={`issue-item ${issue.severity}`}>
                <div className="issue-header">
                  <span className="issue-icon">{getSeverityIcon(issue.severity)}</span>
                  <span className="issue-line">Line {issue.line}</span>
                  <span className={`issue-severity ${issue.severity}`}>
                    {issue.severity.toUpperCase()}
                  </span>
                </div>
                <div className="issue-message">{issue.message}</div>
                {issue.suggestion && (
                  <div className="issue-suggestion">
                    <strong>Suggestion:</strong> {issue.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {code && (
        <div className="code-preview-section">
          <h3>Code with Issues Highlighted</h3>
          <div className="code-preview-container">
            <Editor
              height="400px"
              language="python"
              value={code}
              theme="vs-light"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                glyphMargin: true,
                renderValidationDecorations: 'on',
                markers: markers,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewResults;
