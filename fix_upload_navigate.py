import re

with open("frontend/src/pages/Upload.tsx", "r") as f:
    content = f.read()

if "useNavigate" not in content:
    content = content.replace("import { useGlobalState } from '../context';", "import { useGlobalState } from '../context';\nimport { useNavigate } from 'react-router-dom';")

content = content.replace("export const UploadDataset: React.FC = () => {", "export const UploadDataset: React.FC = () => {\n  const navigate = useNavigate();")

content = content.replace("window.location.href = '/';", "navigate('/');")

with open("frontend/src/pages/Upload.tsx", "w") as f:
    f.write(content)
