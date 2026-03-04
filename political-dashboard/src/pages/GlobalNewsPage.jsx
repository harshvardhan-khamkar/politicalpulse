import React from 'react';
import NewspaperPage from '../components/NewspaperPage';

const GlobalNewsPage = () => (
    <NewspaperPage
        endpoint="/news/global"
        edition="Global Geopolitical Edition"
    />
);

export default GlobalNewsPage;
