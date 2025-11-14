import { render, screen } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App';

test('renders Foodgram application', () => {
  render(
    <Router>
      <App />
    </Router>
  );
  
  // Проверяем что основные элементы отображаются
  expect(screen.getByRole('banner')).toBeInTheDocument(); // header
  expect(screen.getByRole('main')).toBeInTheDocument();   // main content
  expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
});