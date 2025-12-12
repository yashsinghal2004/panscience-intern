'use client'

import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'

interface ChartWrapperProps {
  type: 'pie' | 'bar' | 'line'
  data: any[]
  colors?: string[]
  height?: number
  dataKey?: string
  xKey?: string
  showGradient?: boolean
}

// Vibrant color palettes for different chart types
const PIE_COLORS = [
  '#667eea', '#764ba2', '#f093fb', '#4facfe', 
  '#00f2fe', '#f6d365', '#fda085', '#96e6a1',
  '#a8edea', '#fed6e3', '#ffecd2', '#fcb69f'
]

const BAR_COLORS = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
  'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)'
]

const BAR_SOLID_COLORS = [
  '#667eea', '#f093fb', '#4facfe', '#43e97b', 
  '#fa709a', '#30cfd0', '#a8edea', '#ff9a9e'
]

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        padding: '12px',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      }}>
        <p style={{ margin: '0 0 8px 0', fontWeight: 600, color: '#333' }}>{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ margin: '4px 0', color: entry.color }}>
            <span style={{ fontWeight: 600 }}>{entry.name || 'Value'}:</span> {entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function ChartWrapper({ 
  type, 
  data, 
  colors = PIE_COLORS, 
  height = 300,
  dataKey = 'count',
  xKey = 'date',
  showGradient = false
}: ChartWrapperProps) {
  if (!data || data.length === 0) {
    return (
      <div style={{ 
        height: `${height}px`, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        color: '#999',
        fontSize: '1rem'
      }}>
        No data available
      </div>
    )
  }

  if (type === 'pie') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ category, count, percent }) => 
              `${category}: ${count || (percent * 100).toFixed(0)}%`
            }
            outerRadius={height * 0.3}
            innerRadius={height * 0.15}
            fill="#8884d8"
            dataKey={dataKey}
            paddingAngle={2}
          >
            {data.map((entry: any, index: number) => (
              <Cell 
                key={`cell-${index}`} 
                fill={colors[index % colors.length]}
                stroke="#fff"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value: string) => (
              <span style={{ color: '#333', fontSize: '0.9rem' }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  if (type === 'bar') {
    // Determine if we should use gradient bars based on data
    const useGradient = showGradient || xKey === 'name' || xKey === 'topic'
    
    // Gradient color mappings
    const gradientStops = [
      { start: '#667eea', end: '#764ba2' },
      { start: '#f093fb', end: '#f5576c' },
      { start: '#4facfe', end: '#00f2fe' },
      { start: '#43e97b', end: '#38f9d7' },
      { start: '#fa709a', end: '#fee140' },
      { start: '#30cfd0', end: '#330867' },
      { start: '#a8edea', end: '#fed6e3' },
      { start: '#ff9a9e', end: '#fecfef' }
    ]
    
    // Add color to each data point for gradient bars
    const dataWithColors = useGradient 
      ? data.map((item, index) => ({
          ...item,
          fill: `url(#colorGradient${index % gradientStops.length})`
        }))
      : data
    
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart 
          data={dataWithColors}
          margin={{ top: 20, right: 30, left: 20, bottom: xKey === 'query' ? 60 : 20 }}
        >
          <defs>
            {gradientStops.map((gradient, index) => (
              <linearGradient key={index} id={`colorGradient${index}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={gradient.start} stopOpacity={1}/>
                <stop offset="100%" stopColor={gradient.end} stopOpacity={1}/>
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" opacity={0.3} />
          <XAxis 
            dataKey={xKey} 
            angle={xKey === 'query' ? -45 : 0} 
            textAnchor={xKey === 'query' ? 'end' : 'start'} 
            height={xKey === 'query' ? 100 : undefined}
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#999' }}
          />
          <YAxis 
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#999' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey={dataKey}
            radius={[8, 8, 0, 0]}
            fill={useGradient ? undefined : BAR_SOLID_COLORS[0]}
          >
            {useGradient && data.map((entry: any, index: number) => (
              <Cell 
                key={`cell-${index}`} 
                fill={`url(#colorGradient${index % gradientStops.length})`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart 
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <defs>
            <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#667eea" stopOpacity={0.3}/>
              <stop offset="100%" stopColor="#667eea" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" opacity={0.3} />
          <XAxis 
            dataKey={xKey}
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#999' }}
          />
          <YAxis 
            tick={{ fill: '#666', fontSize: 12 }}
            tickLine={{ stroke: '#999' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            formatter={(value: string) => (
              <span style={{ color: '#333', fontSize: '0.9rem' }}>{value}</span>
            )}
          />
          <Line 
            type="monotone" 
            dataKey={dataKey} 
            stroke="#667eea" 
            strokeWidth={3}
            dot={{ fill: '#667eea', r: 5, strokeWidth: 2, stroke: '#fff' }}
            activeDot={{ r: 7, stroke: '#667eea', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return null
}
