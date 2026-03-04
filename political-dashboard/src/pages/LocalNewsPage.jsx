import React from 'react';
import NewspaperPage from '../components/NewspaperPage';

const LocalNewsPage = () => (
    <NewspaperPage
        endpoint="/news/local"
        edition="Indian Political Edition"
    />
);

export default LocalNewsPage;
