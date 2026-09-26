import React, { createContext, useContext, useState } from 'react';

type GlobalStateContextType = {
  runId: string;
  setRunId: (id: string) => void;
};

const GlobalStateContext = createContext<GlobalStateContextType | undefined>(undefined);

export const GlobalStateProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [runId, setRunId] = useState<string>('initial');
  return (
    <GlobalStateContext.Provider value={{ runId, setRunId }}>
      {children}
    </GlobalStateContext.Provider>
  );
};

export const useGlobalState = () => {
  const ctx = useContext(GlobalStateContext);
  if (!ctx) throw new Error("Missing GlobalStateProvider");
  return ctx;
};
