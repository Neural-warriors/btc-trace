import re

with open("frontend/src/App.tsx", "r") as f:
    content = f.read()

content = content.replace("import { Sidebar } from './components/Sidebar';", "import { Sidebar } from './components/Sidebar';\nimport { GlobalStateProvider } from './context';")
content = content.replace("<Router>", "<GlobalStateProvider>\n      <Router>")
content = content.replace("</Router>", "</Router>\n      </GlobalStateProvider>")

with open("frontend/src/App.tsx", "w") as f:
    f.write(content)
