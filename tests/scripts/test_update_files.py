import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from github import Github, Repository, GitRef, Commit, GitTree, GitCommit

# Add the scripts directory to the Python path
sys.path.append(os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    '.github', 'scripts'
))

from update_files import update_workflow_files, update_file_content

@pytest.fixture
def mock_github():
    """Create a mock Github instance"""
    with patch('github.Github') as mock:
        # Setup mock repository
        mock_repo = MagicMock(spec=Repository.Repository)
        mock_repo.get_git_ref.return_value = MagicMock(spec=GitRef.GitRef)
        mock_repo.get_commits.return_value = [
            MagicMock(spec=Commit.Commit)
        ]
        
        # Setup mock Git objects
        mock_repo.create_git_blob.return_value = MagicMock(sha='test_blob_sha')
        mock_repo.create_git_tree.return_value = MagicMock(spec=GitTree.GitTree)
        mock_repo.create_git_commit.return_value = MagicMock(
            spec=GitCommit.GitCommit,
            sha='test_commit_sha'
        )
        
        # Setup mock Github instance
        instance = mock.return_value
        instance.get_repo.return_value = mock_repo
        
        yield mock

def test_update_workflow_files(mock_github):
    """Test workflow file update process"""
    with patch.dict('os.environ', {
        'GITHUB_TOKEN': 'test_token',
        'GITHUB_REPOSITORY': 'test/repo'
    }):
        update_workflow_files()
        
        # Verify Github was initialized with token
        mock_github.assert_called_once_with('test_token')
        
        # Get mock repository instance
        mock_repo = mock_github.return_value.get_repo.return_value
        
        # Verify repository operations were called
        mock_repo.get_git_ref.assert_called_once()
        mock_repo.get_commits.assert_called_once()
        mock_repo.create_git_tree.assert_called_once()
        mock_repo.create_git_commit.assert_called_once()

def test_update_file_content():
    """Test file content update logic"""
    test_content = "test content"
    updated_content = update_file_content(test_content)
    assert isinstance(updated_content, str)