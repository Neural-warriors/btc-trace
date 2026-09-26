import re

with open("frontend/src/pages/Upload.tsx", "r") as f:
    content = f.read()

replacement = """              onChange={async (e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setLoading(true);
                  try {
                    const res = await client.uploadDataset(e.target.files[0]);
                    const datasetId = res.dataset_id;
                    const runId = res.run_id;
                    
                    const pollStatus = async () => {
                      try {
                        const statusRes = await client.checkStatus(datasetId, runId);
                        if (statusRes.status === 'ready') {
                          setRunId(runId);
                          window.location.href = '/';
                        } else if (statusRes.status === 'failed') {
                          setError(true);
                          setLoading(false);
                          alert("Processing failed on the backend.");
                        } else {
                          setTimeout(pollStatus, 2000);
                        }
                      } catch(err) {
                        setTimeout(pollStatus, 2000);
                      }
                    };
                    
                    setTimeout(pollStatus, 2000);
                    
                  } catch(err) {
                    console.error("Upload error", err);
                    setError(true);
                    setLoading(false);
                  }
                }
              }}"""

content = re.sub(r"              onChange=\{async \(e\) => \{.*?\}\}", replacement, content, flags=re.DOTALL)

with open("frontend/src/pages/Upload.tsx", "w") as f:
    f.write(content)
