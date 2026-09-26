import re

with open("frontend/src/pages/Overview.tsx", "r") as f:
    content = f.read()

# Replace the input onChange handler
new_on_change = """onChange={async (e) => {
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
                            window.location.reload(); // Hard reload guarantees cache clearing across the entire React app
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

# Regex to find the input block
# It looks like:
#                 onChange={async (e) => {
# ...
#                 }}
content = re.sub(r"onChange=\{async \(e\) => \{.*?\n\s*\}\}", new_on_change, content, flags=re.DOTALL)

with open("frontend/src/pages/Overview.tsx", "w") as f:
    f.write(content)
