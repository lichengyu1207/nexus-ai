import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

const Pagination: React.FC<PaginationProps> = ({ currentPage, totalPages, onPageChange, className = '' }) => {
  const pages = [];
  const maxVisible = 5;
  
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);
  
  if (endPage - startPage + 1 < maxVisible) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <nav className={`flex items-center justify-center space-x-1 ${className}`}>
      <PaginationPrevious
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      />
      
      {startPage > 1 && (
        <>
          <PaginationItem onClick={() => onPageChange(1)}>1</PaginationItem>
          {startPage > 2 && <PaginationEllipsis />}
        </>
      )}
      
      {pages.map((page) => (
        <PaginationItem
          key={page}
          active={page === currentPage}
          onClick={() => onPageChange(page)}
        >
          {page}
        </PaginationItem>
      ))}
      
      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <PaginationEllipsis />}
          <PaginationItem onClick={() => onPageChange(totalPages)}>
            {totalPages}
          </PaginationItem>
        </>
      )}
      
      <PaginationNext
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      />
    </nav>
  );
};

const PaginationItem: React.FC<{
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}> = ({ children, active = false, onClick }) => (
  <button
    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      active
        ? 'bg-primary-600 text-white'
        : 'text-gray-700 hover:bg-gray-100'
    } ${onClick ? 'cursor-pointer' : ''}`}
    onClick={onClick}
  >
    {children}
  </button>
);

const PaginationPrevious: React.FC<{ onClick?: () => void; disabled?: boolean }> = ({ onClick, disabled }) => (
  <button
    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      disabled
        ? 'text-gray-400 cursor-not-allowed'
        : 'text-gray-700 hover:bg-gray-100 cursor-pointer'
    }`}
    onClick={onClick}
    disabled={disabled}
  >
    上一页
  </button>
);

const PaginationNext: React.FC<{ onClick?: () => void; disabled?: boolean }> = ({ onClick, disabled }) => (
  <button
    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      disabled
        ? 'text-gray-400 cursor-not-allowed'
        : 'text-gray-700 hover:bg-gray-100 cursor-pointer'
    }`}
    onClick={onClick}
    disabled={disabled}
  >
    下一页
  </button>
);

const PaginationEllipsis: React.FC = () => (
  <span className="px-2 text-gray-400">...</span>
);

const PaginationContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <ul className={`flex items-center space-x-1 ${className}`}>
    {React.Children.map(children, (child) => (
      <li>{child}</li>
    ))}
  </ul>
);

const PaginationLink: React.FC<{
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
  className?: string;
}> = ({ children, active = false, onClick, className = '' }) => (
  <button
    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
      active
        ? 'bg-primary-600 text-white'
        : 'text-gray-700 hover:bg-gray-100'
    } ${onClick ? 'cursor-pointer' : ''} ${className}`}
    onClick={onClick}
  >
    {children}
  </button>
);

export default Pagination;
export {
  Pagination,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  PaginationEllipsis,
  PaginationContent,
  PaginationLink,
};
