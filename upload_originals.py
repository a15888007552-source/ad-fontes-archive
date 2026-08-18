import base64, json, os, subprocess, glob

repo = "a15888007552-source/ad-fontes-archive"
names = sorted(os.path.basename(p) for p in glob.glob("assets/photos/original/*"))
print("files:", len(names), flush=True)

def gh(args, inp=None):
    cmd = ["gh", "api", *args]
    if inp is not None:
        cmd += ["--input", inp]
    return subprocess.check_output(cmd).decode().strip()

head = gh(["repos/%s/git/ref/heads/main" % repo, "--jq", ".object.sha"])
base_tree = json.loads(gh(["repos/%s/git/commits/%s" % (repo, head), "--jq", "{t: .tree.sha}"]))["t"]
print("head:", head[:7], "base_tree:", base_tree[:7], flush=True)

blobs = []
for i, n in enumerate(names):
    data = base64.b64encode(open("assets/photos/original/" + n, "rb").read()).decode()
    body = json.dumps({"content": data, "encoding": "base64"})
    with open("/tmp/blob.json", "w") as fp:
        fp.write(body)
    sha = json.loads(gh(["repos/%s/git/blobs" % repo], "/tmp/blob.json"))["sha"]
    blobs.append({"path": "assets/photos/original/" + n, "mode": "100644", "type": "blob", "sha": sha})
    if (i + 1) % 50 == 0 or i + 1 == len(names):
        print("blobs:", i + 1, "/", len(names), flush=True)

tree_body = json.dumps({"base_tree": base_tree, "tree": blobs})
with open("/tmp/tree.json", "w") as fp:
    fp.write(tree_body)
new_tree = json.loads(gh(["repos/%s/git/trees" % repo], "/tmp/tree.json"))["sha"]
print("new_tree:", new_tree[:7], flush=True)

commit_body = json.dumps({"message": "ingest: 426 张相机原图（assets/photos/original）", "tree": new_tree, "parents": [head]})
with open("/tmp/commit.json", "w") as fp:
    fp.write(commit_body)
new_commit = json.loads(gh(["repos/%s/git/commits" % repo], "/tmp/commit.json"))["sha"]
print("new_commit:", new_commit[:7], flush=True)

ref_body = json.dumps({"sha": new_commit, "force": False})
with open("/tmp/ref.json", "w") as fp:
    fp.write(ref_body)
gh(["repos/%s/git/refs/heads/main" % repo, "-X", "PATCH"], "/tmp/ref.json")
print("PUSHED", flush=True)