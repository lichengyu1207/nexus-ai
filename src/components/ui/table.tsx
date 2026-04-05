import React from 'react';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

const Table: React.FC<TableProps> = ({ children, className = '' }) => (
  <div className={`relative w-full overflow-auto ${className}`}>
    <table className="w-full caption-bottom text-sm">
      {children}
    </table>
  </div>
);

const TableHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <thead className={`[&_tr]:border-b ${className}`}>
    {children}
  </thead>
);

const TableBody: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <tbody className={`[&_tr:last-child]:border-0 ${className}`}>
    {children}
  </tbody>
);

const TableFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <tfoot className={`border-t bg-gray-50/50 font-medium [&>tr]:last:border-b-0 ${className}`}>
    {children}
  </tfoot>
);

const TableRow: React.FC<{ children: React.ReactNode; className?: string; onClick?: () => void }> = ({ children, className = '', onClick }) => (
  <tr
    className={`border-b transition-colors hover:bg-gray-50/50 data-[state=selected]:bg-gray-100 ${onClick ? 'cursor-pointer' : ''} ${className}`}
    onClick={onClick}
  >
    {children}
  </tr>
);

const TableHead: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <th className={`h-12 px-4 text-left align-middle font-medium text-gray-500 [&:has([role=checkbox])]:pr-0 ${className}`}>
    {children}
  </th>
);

const TableCell: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <td className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`}>
    {children}
  </td>
);

const TableCaption: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <caption className={`mt-4 text-sm text-gray-500 ${className}`}>
    {children}
  </caption>
);

export default Table;
export { Table, TableHeader, TableBody, TableFooter, TableRow, TableHead, TableCell, TableCaption };
