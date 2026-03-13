import logging

logger = logging.getLogger(__name__)

def collect_mock_data():
    """
    Mock data collector that could be replaced with actual PRAW or Twitter API hooks.
    """
    logger.info("Collecting mock social media data...")
    return [
        {"author": "user1", "text": "I can't believe the current state of politics. Total chaos!"},
        {"author": "user2", "text": "Healthcare must be our top priority this election cycle."},
        {"author": "user3", "text": "Taxes are too high. We need serious fiscal reform."},
        {"author": "user4", "text": "Climate change policies are destroying the energy sector jobs."},
        {"author": "user5", "text": "We need to protect the environment for future generations by investing in renewables!"}
    ]
