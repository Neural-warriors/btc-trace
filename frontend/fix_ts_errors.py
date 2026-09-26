import os, glob, re

files = glob.glob("src/**/*.tsx", recursive=True)
for file in files:
    with open(file, "r") as f:
        content = f.read()
    
    if "ErrorBoundary.tsx" in file:
        content = content.replace("import React, { Component, ErrorInfo, ReactNode } from 'react';", "import { Component, ErrorInfo, ReactNode } from 'react';")
    
    if "Upload.tsx" in file:
        content = content.replace("const { runId, setRunId } = useGlobalState();", "const { setRunId } = useGlobalState();")
    
    if "EntityDetail.tsx" in file or "Search.tsx" in file:
        content = re.sub(r"\s*const \{ runId, setRunId \} = useGlobalState\(\);", "", content)
    else:
        # replace `const { runId, setRunId } = useGlobalState();` with `const { runId } = useGlobalState();` for pages that only read it
        if "Overview.tsx" not in file and "Upload.tsx" not in file:
            content = content.replace("const { runId, setRunId } = useGlobalState();", "const { runId } = useGlobalState();")

    with open(file, "w") as f:
        f.write(content)
