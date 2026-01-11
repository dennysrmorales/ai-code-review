import React from 'react';
import Editor from '@monaco-editor/react';

const CodeEditor = ({ value, onChange, language }) => {
  const handleEditorChange = (newValue) => {
    onChange(newValue || '');
  };

  const languageMap = {
    python: 'python',
    javascript: 'javascript',
    typescript: 'typescript',
    java: 'java',
    cpp: 'cpp',
    c: 'c',
    go: 'go',
    rust: 'rust',
  };

  return (
    <div style={{ flex: 1, minHeight: '500px', border: '1px solid #ddd', borderRadius: '4px' }}>
      <Editor
        height="100%"
        language={languageMap[language] || 'python'}
        value={value}
        onChange={handleEditorChange}
        theme="vs-light"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          wordWrap: 'on',
          automaticLayout: true,
          scrollBeyondLastLine: false,
          padding: { top: 10, bottom: 10 },
        }}
      />
    </div>
  );
};

export default CodeEditor;
