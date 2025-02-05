import os
import base64
from typing import Optional, Dict, Any
from github import Github
from github.Repository import Repository
from github.ContentFile import ContentFile


class GitHubFileOps:
    """
    Utility class for GitHub file operations with proper encoding handling.
    """

    def __init__(self, token: str, repo_name: str):
        """
        Initialize with GitHub credentials and repository info.

        Args:
            token: GitHub personal access token
            repo_name: Full repository name (owner/repo)
        """
        self.g = Github(token)
        self.repo: Repository = self.g.get_repo(repo_name)

    def get_file_info(
        self, path: str, ref: Optional[str] = None
    ) -> Optional[ContentFile]:
        """
        Get file information including SHA.

        Args:
            path: File path in repository
            ref: Branch or commit SHA (optional)

        Returns:
            ContentFile object if file exists, None otherwise
        """
        try:
            return self.repo.get_contents(path, ref=ref)
        except Exception:
            return None

    def create_or_update_file(
        self, path: str, content: str, message: str, branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create or update a file with proper base64 encoding.

        Args:
            path: File path in repository
            content: File content (plain text)
            message: Commit message
            branch: Branch name (default: main)

        Returns:
            Dict containing API response
        """
        try:
            # Encode content
            encoded_content = base64.b64encode(content.encode()).decode()

            # Get existing file info
            file_info = self.get_file_info(path, branch)

            if file_info:
                # Update existing file
                result = self.repo.update_file(
                    path=path,
                    message=message,
                    content=encoded_content,
                    sha=file_info.sha,
                    branch=branch,
                )
                return {
                    "success": True,
                    "commit": result["commit"].sha,
                    "content": result["content"].sha,
                }
            else:
                # Create new file
                result = self.repo.create_file(
                    path=path, message=message, content=encoded_content, branch=branch
                )
                return {
                    "success": True,
                    "commit": result["commit"].sha,
                    "content": result["content"].sha,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """Main entry point for CLI usage"""
    # Get environment variables
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    path = os.environ["FILE_PATH"]
    message = os.environ["COMMIT_MESSAGE"]
    content = os.environ["FILE_CONTENT"]
    branch = os.environ.get("BRANCH", "main")

    # Initialize file operations
    file_ops = GitHubFileOps(token, repo)

    # Perform update
    result = file_ops.create_or_update_file(
        path=path, content=content, message=message, branch=branch
    )

    if result["success"]:
        print("File operation successful!")
        print(f"Commit SHA: {result['commit']}")
        print(f"Content SHA: {result['content']}")
    else:
        print(f"Error: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()
