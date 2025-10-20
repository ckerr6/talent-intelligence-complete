# ABOUTME: Unit tests for migration utility functions
# ABOUTME: Tests normalization, validation, and matching logic

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "migration_scripts"))
from migration_utils import (
    normalize_linkedin_url,
    normalize_email,
    validate_email,
    infer_email_type,
    calculate_match_score,
    name_similarity,
    generate_person_id
)


@pytest.mark.unit
class TestLinkedInNormalization:
    """Test LinkedIn URL normalization"""
    
    def test_normalize_basic_url(self):
        url = "https://www.linkedin.com/in/john-smith/"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/john-smith"
    
    def test_normalize_url_without_protocol(self):
        url = "linkedin.com/in/john-smith"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/john-smith"
    
    def test_normalize_url_without_www(self):
        url = "https://linkedin.com/in/john-smith/"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/john-smith"
    
    def test_normalize_url_with_query_params(self):
        url = "https://www.linkedin.com/in/john-smith/?trk=something"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/john-smith"
    
    def test_normalize_url_encoded(self):
        url = "https://www.linkedin.com/in/%c3%a1lvaro-g-68840515b"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/álvaro-g-68840515b"
    
    def test_normalize_with_trailing_slash(self):
        url = "https://www.linkedin.com/in/john-smith/"
        result = normalize_linkedin_url(url)
        assert result == "linkedin.com/in/john-smith"
    
    def test_normalize_none(self):
        result = normalize_linkedin_url(None)
        assert result is None
    
    def test_normalize_empty_string(self):
        result = normalize_linkedin_url("")
        assert result is None
    
    def test_normalize_invalid_url(self):
        url = "not a linkedin url"
        result = normalize_linkedin_url(url)
        assert result == "not a linkedin url"  # Returns as-is if no pattern match


@pytest.mark.unit
class TestEmailNormalization:
    """Test email address normalization"""
    
    def test_normalize_basic_email(self):
        email = "John.Smith@Company.COM"
        result = normalize_email(email)
        assert result == "john.smith@company.com"
    
    def test_normalize_with_whitespace(self):
        email = "  user@example.com  "
        result = normalize_email(email)
        assert result == "user@example.com"
    
    def test_normalize_none(self):
        result = normalize_email(None)
        assert result is None
    
    def test_normalize_empty_string(self):
        result = normalize_email("")
        assert result is None
    
    def test_normalize_invalid_email_no_at(self):
        email = "notanemail.com"
        result = normalize_email(email)
        assert result is None
    
    def test_normalize_invalid_email_no_dot(self):
        email = "user@nodot"
        result = normalize_email(email)
        assert result is None


@pytest.mark.unit
class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_email(self):
        assert validate_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        assert validate_email("user@mail.example.com") is True
    
    def test_valid_email_with_plus(self):
        assert validate_email("user+tag@example.com") is True
    
    def test_valid_email_with_dots(self):
        assert validate_email("first.last@example.com") is True
    
    def test_invalid_email_no_at(self):
        assert validate_email("notanemail.com") is False
    
    def test_invalid_email_no_domain(self):
        assert validate_email("user@") is False
    
    def test_invalid_email_no_username(self):
        assert validate_email("@example.com") is False
    
    def test_invalid_email_spaces(self):
        assert validate_email("user @example.com") is False
    
    def test_invalid_email_none(self):
        assert validate_email(None) is False
    
    def test_invalid_email_empty(self):
        assert validate_email("") is False


@pytest.mark.unit
class TestEmailTypeInference:
    """Test email type inference"""
    
    def test_personal_gmail(self):
        result = infer_email_type("user@gmail.com")
        assert result == "personal"
    
    def test_personal_yahoo(self):
        result = infer_email_type("user@yahoo.com")
        assert result == "personal"
    
    def test_personal_hotmail(self):
        result = infer_email_type("user@hotmail.com")
        assert result == "personal"
    
    def test_work_email(self):
        result = infer_email_type("user@company.com")
        assert result == "work"
    
    def test_github_noreply(self):
        result = infer_email_type("user@users.noreply.github.com")
        assert result == "unknown"
    
    def test_noreply_email(self):
        result = infer_email_type("noreply@example.com")
        assert result == "unknown"
    
    def test_none_email(self):
        result = infer_email_type(None)
        assert result == "unknown"


@pytest.mark.unit
class TestMatchScore:
    """Test duplicate detection match scoring"""
    
    def test_perfect_linkedin_match(self):
        record1 = {'linkedin_url': 'https://www.linkedin.com/in/john-smith'}
        record2 = {'linkedin_url': 'https://linkedin.com/in/john-smith/'}
        score = calculate_match_score(record1, record2)
        assert score >= 0.5
    
    def test_perfect_email_match(self):
        record1 = {'email': 'john@example.com'}
        record2 = {'email': 'John@Example.COM'}
        score = calculate_match_score(record1, record2)
        assert score >= 0.3
    
    def test_perfect_name_match(self):
        record1 = {'full_name': 'John Smith'}
        record2 = {'full_name': 'john smith'}
        score = calculate_match_score(record1, record2)
        assert score >= 0.15
    
    def test_company_match(self):
        record1 = {'company': 'Acme Corp'}
        record2 = {'company': 'Acme'}
        score = calculate_match_score(record1, record2)
        assert score >= 0.05
    
    def test_multiple_matches(self):
        record1 = {
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'email': 'john@example.com',
            'full_name': 'John Smith'
        }
        record2 = {
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'email': 'john@example.com',
            'full_name': 'John Smith'
        }
        score = calculate_match_score(record1, record2)
        assert score >= 0.95  # Should be very high
    
    def test_no_match(self):
        record1 = {'linkedin_url': 'https://linkedin.com/in/john-smith'}
        record2 = {'linkedin_url': 'https://linkedin.com/in/jane-doe'}
        score = calculate_match_score(record1, record2)
        assert score < 0.5


@pytest.mark.unit
class TestNameSimilarity:
    """Test name similarity calculation"""
    
    def test_identical_names(self):
        similarity = name_similarity("John Smith", "John Smith")
        assert similarity > 0.9
    
    def test_case_insensitive(self):
        similarity = name_similarity("John Smith", "john smith")
        assert similarity > 0.9
    
    def test_similar_names(self):
        similarity = name_similarity("John Smith", "Jon Smith")
        assert 0.5 < similarity < 1.0
    
    def test_different_names(self):
        similarity = name_similarity("John Smith", "Jane Doe")
        assert similarity < 0.5
    
    def test_empty_names(self):
        similarity = name_similarity("", "")
        assert similarity == 0.0
    
    def test_none_names(self):
        similarity = name_similarity(None, None)
        assert similarity == 0.0


@pytest.mark.unit
class TestGeneratePersonId:
    """Test person ID generation"""
    
    def test_generate_with_linkedin(self):
        person_id = generate_person_id(
            linkedin_url="https://linkedin.com/in/john-smith"
        )
        assert person_id is not None
        assert len(person_id) == 36  # UUID format
    
    def test_generate_with_email(self):
        person_id = generate_person_id(
            email="john@example.com"
        )
        assert person_id is not None
        assert len(person_id) == 36
    
    def test_generate_with_name(self):
        person_id = generate_person_id(
            full_name="John Smith"
        )
        assert person_id is not None
        assert len(person_id) == 36
    
    def test_consistent_generation(self):
        """Same inputs should generate same ID"""
        id1 = generate_person_id(
            linkedin_url="https://linkedin.com/in/john-smith",
            email="john@example.com"
        )
        id2 = generate_person_id(
            linkedin_url="https://linkedin.com/in/john-smith",
            email="john@example.com"
        )
        assert id1 == id2
    
    def test_different_inputs_different_ids(self):
        id1 = generate_person_id(email="john@example.com")
        id2 = generate_person_id(email="jane@example.com")
        assert id1 != id2
    
    def test_fallback_to_random(self):
        """Should generate random UUID if no identifiers"""
        person_id = generate_person_id()
        assert person_id is not None
        assert len(person_id) == 36

