export interface CarItem {
  id: string;
  expectedPart: string;
  actualPart: string;
  outcome: string;
  image: string;
  resultImage: string;
  date: string;
  isQueued: boolean;
}

export interface ChartOptions {
  responsive: boolean;
  maintainAspectRatio: boolean;
  plugins?: {
    legend?: {
      position?: 'top' | 'bottom' | 'left' | 'right';
      labels?: {
        color?: string;
        font?: {
          size?: number;
          family?: string;
        };
      };
    };
  };
  scales?: {
    y?: {
      beginAtZero?: boolean;
      grid?: {
        color?: string;
      };
      ticks?: {
        color?: string;
        font?: {
          size?: number;
          family?: string;
        };
      };
    };
    x?: {
      grid?: {
        color?: string;
      };
      ticks?: {
        color?: string;
        font?: {
          size?: number;
          family?: string;
        };
      };
    };
  };
}

export interface AppConfig {
  min_conf_threshold: number;
  connection_type: 'PLC' | 'GALC';
  plc_host: string;
  plc_port: number;
  galc_host: string;
  galc_port: number;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
  message?: string;
} 