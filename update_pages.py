import os
import re

def update_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Skip if already updated
    if "useGlobalState" in content:
        return

    # Add import
    import_match = re.search(r"import React, { useEffect, useState } from 'react';", content)
    if import_match:
        content = content.replace("import React, { useEffect, useState } from 'react';", "import React, { useEffect, useState } from 'react';\nimport { useGlobalState } from '../context';")
    else:
        # Fallback
        content = "import { useGlobalState } from '../context';\n" + content

    # Add hook at the top of the component
    # Assume components are defined as `export const Name: React.FC = () => {`
    comp_match = re.search(r"export const \w+: React\.FC(<any>)? = \(\) => {", content)
    if comp_match:
        hook_insert = comp_match.group(0) + "\n  const { runId, setRunId } = useGlobalState();"
        content = content.replace(comp_match.group(0), hook_insert)
        
    # Update useEffect dependencies to include runId
    content = re.sub(r"useEffect\(\(\) => \{(.*?)\}, \[\]\);", r"useEffect(() => {\1}, [runId]);", content, flags=re.DOTALL)
    
    # In Overview.tsx, replace window.location.reload() with setRunId(runId)
    if "Overview.tsx" in filepath:
        content = content.replace("window.location.reload(); // Hard reload guarantees cache clearing across the entire React app", "setRunId(runId);")
        
    with open(filepath, "w") as f:
        f.write(content)

pages_dir = "frontend/src/pages"
for filename in os.listdir(pages_dir):
    if filename.endswith(".tsx") and filename not in ["Sidebar.tsx", "Layout.tsx"]:
        update_file(os.path.join(pages_dir, filename))
        
print("Updated pages.")
