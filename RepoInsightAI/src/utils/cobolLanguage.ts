// COBOL language configuration for Monaco Editor
export const cobolLanguageConfig = {
  comments: {
    lineComment: '*',
  },
  brackets: [
    ['(', ')'],
  ],
  autoClosingPairs: [
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
  surroundingPairs: [
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
};

// COBOL syntax highlighting rules
export const cobolTokenProvider = {
  defaultToken: '',
  ignoreCase: true,

  tokenizer: {
    root: [
      // Comments
      [/^\s*\*.*$/, 'comment'],
      
      // Division headers
      [/\b(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b/i, 'keyword'],
      
      // Section headers  
      [/\b(CONFIGURATION|INPUT-OUTPUT|FILE|WORKING-STORAGE|LINKAGE|LOCAL-STORAGE)\s+SECTION\b/i, 'keyword'],
      
      // Common COBOL keywords
      [/\b(PROGRAM-ID|AUTHOR|DATE-WRITTEN|DATE-COMPILED|MOVE|TO|FROM|PERFORM|CALL|IF|ELSE|END-IF|DISPLAY|ACCEPT|ADD|SUBTRACT|MULTIPLY|DIVIDE|COMPUTE|OPEN|CLOSE|READ|WRITE|STOP|RUN|EXIT|PICTURE|PIC|VALUE|OCCURS|REDEFINES|COPY|SELECT|ASSIGN|ORGANIZATION|ACCESS|RECORD|KEY|FILE|STATUS|FD|01|05|10|15|20|25|30|35|40|45|50|55|60|65|70|75|80|85|90|95)\b/i, 'keyword'],
      
      // Numbers
      [/\b\d+(\.\d+)?\b/, 'number'],
      
      // Strings
      [/"[^"]*"/, 'string'],
      [/'[^']*'/, 'string'],
      
      // Picture clauses
      [/\bPIC(TURE)?\s+[X9AV\(\)\.S\+\-\$Z\*,\/]+/i, 'type'],
      
      // Level numbers at start of line
      [/^\s*\d{2}\s+/, 'number'],
      
      // Identifiers
      [/[a-zA-Z][\w-]*/, 'identifier'],
      
      // Operators and punctuation
      [/[=<>]/, 'operator'],
      [/[().]/, 'delimiter'],
    ],
  },
};

// Function to register COBOL language with Monaco Editor
export const registerCobolLanguage = (monaco: any) => {
  // Register the language
  monaco.languages.register({ id: 'cobol' });
  
  // Set the language configuration
  monaco.languages.setLanguageConfiguration('cobol', cobolLanguageConfig);
  
  // Set the syntax highlighting rules
  monaco.languages.setMonarchTokensProvider('cobol', cobolTokenProvider);
};
