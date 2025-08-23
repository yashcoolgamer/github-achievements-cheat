import os
import time

from dotenv import load_dotenv
from git import Repo, Actor

# 加载 .env 文件
load_dotenv()

# 获取作者信息
GITHUB_USERNAME_1 = os.getenv("GITHUB_USERNAME_1")
GITHUB_USER1_EMAIL = os.getenv("GTIHUB_USER1_EMAIL")
GITHUB_USERNAME_2 = os.getenv("GITHUB_USERNAME_2")
GITHUB_USER2_EMAIL = os.getenv("GTIHUB_USER2_EMAIL")

# 从 .env 获取仓库信息
REPO_NAME = os.getenv("REPO_NAME")
REPO_OWNER = os.getenv("REPO_OWNER")
GITHUB_PAT = os.getenv("GITHUB_PAT")
REPO_URL = f"https://{GITHUB_PAT}@github.com/{GITHUB_USERNAME_1}/{REPO_NAME}.git"
REPO_DIR = f"./{REPO_NAME}"

co_authors = [
    {"name": GITHUB_USERNAME_1, "email": GITHUB_USER1_EMAIL},
    {"name": GITHUB_USERNAME_2, "email": GITHUB_USER2_EMAIL}
]

# 提交信息模板
def generate_commit_message(base_msg, co_authors):
    co_lines = "\n".join([f"Co-authored-by: {c['name']} <{c['email']}>" for c in co_authors])
    return f"{base_msg}\n\n{co_lines}"

# 第一次提交
def first_commit(repo_path):
    repo = Repo(repo_path)
    repo.index.add(["test_file.txt"])
    commit_msg = generate_commit_message("Initial Commit", co_authors)
    author = Actor(GITHUB_USERNAME_1, GITHUB_USER1_EMAIL)
    repo.index.commit(commit_msg, author=author)
    origin = repo.remote(name='origin')
    origin.push()

# 多次提交（循环）
def make_commits(repo_path, num_commits=5):
    repo = Repo(repo_path)
    for i in range(num_commits):
        # 创建一个修改文件
        with open(os.path.join(repo_path, "test_file.txt"), "a") as file:
            file.write(f"Commit number {i + 1}\n")
        repo.index.add(["test_file.txt"])
        # 提交信息中添加 co-author
        commit_msg = generate_commit_message(f"Commit #{i + 1}", co_authors)
        # 随机选择一个共同作者作为主导作者
        author_idx = i % len(co_authors)
        author = Actor(co_authors[author_idx]['name'], co_authors[author_idx]['email'])
        # 执行提交
        repo.index.commit(commit_msg, author=author)
        # 推送提交
        origin = repo.remote(name='origin')
        try:
            origin.push()
        except Exception as e:
            print("Push failed:", e)
        print(f"Commit {i + 1} pushed.")
        time.sleep(10)

# 初始化和克隆
if os.path.exists(REPO_DIR):
    import shutil
    shutil.rmtree(REPO_DIR)
repo = Repo.clone_from(REPO_URL, REPO_DIR)
print("Repository cloned.")

# 创建测试文件
test_file_path = os.path.join(REPO_DIR, "test_file.txt")
with open(test_file_path, "w") as file:
    file.write("Hello GitHub!\n")
repo = Repo(REPO_DIR)

# 设置 git config 使用实际的 GitHub 用户信息
repo.config_writer().set_value("user", "name", GITHUB_USERNAME_1).release()
repo.config_writer().set_value("user", "email", GITHUB_USER1_EMAIL).release()

# 第一次提交
first_commit(REPO_DIR)

# 多次提交
make_commits(REPO_DIR, num_commits=48)
print("Done!")
