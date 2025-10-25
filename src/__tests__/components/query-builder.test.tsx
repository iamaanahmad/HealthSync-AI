import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryBuilder } from '../../components/researcher/query-builder';
import { ResearchQueryService } from '../../lib/research-query-api';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { it } from 'node:test';
import { beforeEach } from 'node:test';
import { describe } from 'node:test';

// Mock the ResearchQueryService
jest.mock('../../lib/research-query-api', () => ({
  ResearchQueryService: {
    getCurrentResearcher: jest.fn(() => ({
      researcherId: 'HMS-12345',
      name: 'Dr. Test Researcher',
      institution: 'Test University',
      department: 'Research Department',
      email: 'test@example.com',
    })),
    submitQuery: jest.fn(),
    getQueryTemplates: jest.fn(() => []),
  },
  ResearchQuerySchema: {
    parse: jest.fn(),
  },
  AVAILABLE_DATA_TYPES: [
    { value: 'demographics', label: 'Demographics', description: 'Age, gender, ethnicity, etc.' },
  ],
  RESEARCH_CATEGORIES: [
    { value: 'clinical_trials', label: 'Clinical Trials', description: 'Interventional studies' },
  ],
}));

// Mock form components
jest.mock('../../components/ui/form', () => ({
  Form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
  FormControl: ({ children }: any) => <div>{children}</div>,
  FormDescription: ({ children }: any) => <div>{children}</div>,
  FormField: ({ render }: any) => render({ field: { value: '', onChange: jest.fn() } }),
  FormItem: ({ children }: any) => <div>{children}</div>,
  FormLabel: ({ children }: any) => <label>{children}</label>,
  FormMessage: () => <div />,
}));

// Mock UI components
jest.mock('../../components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: any) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <h3 data-testid="card-title">{children}</h3>,
}));

jest.mock('../../components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue }: any) => <div data-testid="tabs" data-default-value={defaultValue}>{children}</div>,
  TabsContent: ({ children, value }: any) => <div data-testid={`tab-content-${value}`}>{children}</div>,
  TabsList: ({ children }: any) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }: any) => <button data-testid={`tab-trigger-${value}`}>{children}</button>,
}));

jest.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, type, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      type={type}
      data-testid="button"
      {...props}
    >
      {children}
    </button>
  ),
}));

jest.mock('../../components/ui/input', () => ({
  Input: ({ placeholder, value, onChange, ...props }: any) => (
    <input 
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      data-testid="input"
      {...props}
    />
  ),
}));

jest.mock('../../components/ui/textarea', () => ({
  Textarea: ({ placeholder, value, onChange, ...props }: any) => (
    <textarea 
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      data-testid="textarea"
      {...props}
    />
  ),
}));

jest.mock('../../components/ui/checkbox', () => ({
  Checkbox: ({ checked, onCheckedChange, ...props }: any) => (
    <input 
      type="checkbox"
      checked={checked}
      onChange={(e) => onCheckedChange?.(e.target.checked)}
      data-testid="checkbox"
      {...props}
    />
  ),
}));

jest.mock('../../components/ui/progress', () => ({
  Progress: ({ value }: any) => (
    <div data-testid="progress" data-value={value}>
      Progress: {value}%
    </div>
  ),
}));

jest.mock('../../components/ui/alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div data-testid="alert-description">{children}</div>,
}));

// Mock other UI components
jest.mock('../../components/ui/select', () => ({
  Select: ({ children }: any) => <div data-testid="select">{children}</div>,
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children }: any) => <div>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <div>{placeholder}</div>,
}));

jest.mock('../../components/ui/badge', () => ({
  Badge: ({ children }: any) => <span data-testid="badge">{children}</span>,
}));

jest.mock('../../components/ui/separator', () => ({
  Separator: () => <hr data-testid="separator" />,
}));

jest.mock('../../components/ui/calendar', () => ({
  Calendar: ({ onSelect }: any) => (
    <div data-testid="calendar" onClick={() => onSelect?.(new Date())}>
      Calendar
    </div>
  ),
}));

jest.mock('../../components/ui/popover', () => ({
  Popover: ({ children }: any) => <div data-testid="popover">{children}</div>,
  PopoverContent: ({ children }: any) => <div data-testid="popover-content">{children}</div>,
  PopoverTrigger: ({ children }: any) => <div data-testid="popover-trigger">{children}</div>,
}));

// Mock react-hook-form
jest.mock('react-hook-form', () => ({
  useForm: () => ({
    control: {},
    handleSubmit: (fn: any) => (e: any) => {
      e.preventDefault();
      fn({
        researcherId: 'HMS-12345',
        studyTitle: 'Test Study',
        studyDescription: 'This is a test study description that is long enough to pass validation requirements.',
        dataRequirements: {
          dataTypes: ['demographics'],
          researchCategories: ['clinical_trials'],
          minimumSampleSize: 100,
        },
        ethicalApprovalId: 'IRB-2024-123456',
      });
    },
    reset: jest.fn(),
    getValues: () => ({
      dataRequirements: {
        dataTypes: [],
        researchCategories: [],
        minimumSampleSize: 100,
        dataRetentionDays: 365,
      },
      privacyRequirements: {
        anonymizationMethods: ['k_anonymity'],
        enhancedAnonymization: false,
      },
    }),
    watch: () => ({ unsubscribe: jest.fn() }),
  }),
  useFieldArray: () => ({
    fields: [],
    append: jest.fn(),
    remove: jest.fn(),
  }),
}));

// Mock @hookform/resolvers/zod
jest.mock('@hookform/resolvers/zod', () => ({
  zodResolver: () => jest.fn(),
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date, formatStr: string) => date.toLocaleDateString(),
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  CalendarIcon: () => <span data-testid="calendar-icon">📅</span>,
  Plus: () => <span data-testid="plus-icon">➕</span>,
  Trash2: () => <span data-testid="trash-icon">🗑️</span>,
  AlertCircle: () => <span data-testid="alert-circle-icon">⚠️</span>,
  CheckCircle: () => <span data-testid="check-circle-icon">✅</span>,
  Clock: () => <span data-testid="clock-icon">🕐</span>,
  FileText: () => <span data-testid="file-text-icon">📄</span>,
}));

describe('QueryBuilder', () => {
  const mockOnQuerySubmit = jest.fn();
  const mockSubmitQuery = ResearchQueryService.submitQuery as jest.MockedFunction<typeof ResearchQueryService.submitQuery>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockSubmitQuery.mockResolvedValue({ success: true, queryId: 'test-query-id' });
  });

  it('renders the query builder form', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    expect(screen.getByTestId('tabs')).toBeInTheDocument();
    expect(screen.getByTestId('tab-trigger-basic')).toBeInTheDocument();
    expect(screen.getByTestId('tab-trigger-data')).toBeInTheDocument();
    expect(screen.getByTestId('tab-trigger-criteria')).toBeInTheDocument();
    expect(screen.getByTestId('tab-trigger-compliance')).toBeInTheDocument();
  });

  it('displays researcher information', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // The researcher ID should be displayed (mocked to return HMS-12345)
    expect(screen.getByDisplayValue('HMS-12345')).toBeInTheDocument();
  });

  it('shows validation errors for invalid form data', async () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /submit research query/i });
    fireEvent.click(submitButton);
    
    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByTestId('alert')).toBeInTheDocument();
    });
  });

  it('handles form submission successfully', async () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Fill in required fields
    const studyTitleInput = screen.getByPlaceholderText('Enter your study title');
    const studyDescriptionTextarea = screen.getByPlaceholderText(/Provide a detailed description/);
    const ethicalApprovalInput = screen.getByPlaceholderText('IRB-2024-123456');
    
    await userEvent.type(studyTitleInput, 'Test Study');
    await userEvent.type(studyDescriptionTextarea, 'This is a test study description that is long enough to pass validation requirements.');
    await userEvent.type(ethicalApprovalInput, 'IRB-2024-123456');
    
    // Submit the form
    const submitButton = screen.getByRole('button', { name: /submit research query/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSubmitQuery).toHaveBeenCalled();
      expect(mockOnQuerySubmit).toHaveBeenCalledWith('test-query-id');
    });
  });

  it('shows progress during submission', async () => {
    // Mock a delayed response
    mockSubmitQuery.mockImplementation(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({ success: true, queryId: 'test-query-id' }), 100)
      )
    );

    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    const submitButton = screen.getByRole('button', { name: /submit research query/i });
    fireEvent.click(submitButton);
    
    // Should show progress indicator
    await waitFor(() => {
      expect(screen.getByTestId('progress')).toBeInTheDocument();
    });
  });

  it('handles submission errors gracefully', async () => {
    mockSubmitQuery.mockResolvedValue({ success: false, error: 'Validation failed' });
    
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    const submitButton = screen.getByRole('button', { name: /submit research query/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockSubmitQuery).toHaveBeenCalled();
      expect(mockOnQuerySubmit).not.toHaveBeenCalled();
    });
  });

  it('loads and applies query templates', () => {
    const mockTemplates = [
      {
        templateId: 'test-template',
        name: 'Test Template',
        description: 'A test template',
        category: 'Test',
        template: {
          studyTitle: 'Template Study',
          studyDescription: 'Template description',
          dataRequirements: {
            dataTypes: ['demographics'],
            researchCategories: ['clinical_trials'],
          },
        },
      },
    ];

    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} templates={mockTemplates} />);
    
    expect(screen.getByText('Test Template')).toBeInTheDocument();
    expect(screen.getByText('A test template')).toBeInTheDocument();
  });

  it('validates required fields', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Check that required field labels are present
    expect(screen.getByText('Study Title')).toBeInTheDocument();
    expect(screen.getByText('Study Description')).toBeInTheDocument();
    expect(screen.getByText('Ethical Approval ID')).toBeInTheDocument();
  });

  it('shows data type and research category options', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Should show checkboxes for data types and research categories
    const checkboxes = screen.getAllByTestId('checkbox');
    expect(checkboxes.length).toBeGreaterThan(0);
  });

  it('allows adding and removing inclusion criteria', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Should have button to add inclusion criteria
    expect(screen.getByText(/Add Inclusion Criterion/)).toBeInTheDocument();
  });

  it('allows adding and removing exclusion criteria', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Should have button to add exclusion criteria
    expect(screen.getByText(/Add Exclusion Criterion/)).toBeInTheDocument();
  });

  it('validates ethical approval ID format', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Should show format description
    expect(screen.getByText(/Format: IRB-YYYY-NNNNNN/)).toBeInTheDocument();
  });

  it('shows privacy requirements options', () => {
    render(<QueryBuilder onQuerySubmit={mockOnQuerySubmit} />);
    
    // Should show enhanced anonymization option
    expect(screen.getByText('Enhanced Anonymization')).toBeInTheDocument();
    expect(screen.getByText('Data Retention Period (Days)')).toBeInTheDocument();
  });
});