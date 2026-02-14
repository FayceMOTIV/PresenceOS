import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	container: {
  		center: true,
  		padding: '2rem',
  		screens: {
  			'2xl': '1400px'
  		}
  	},
  	extend: {
  		colors: {
  			// shadcn/ui CSS variable colors (keep as-is)
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			// Platform colors
  			instagram: '#E4405F',
  			tiktok: '#000000',
  			linkedin: '#0A66C2',
  			facebook: '#1877F2',
  			// Charts
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			// Extended palette — success/warning/info semantic colors
  			success: {
  				DEFAULT: '#10B981',
  				light: '#D1FAE5',
  				dark: '#065F46',
  			},
  			warning: {
  				DEFAULT: '#F59E0B',
  				light: '#FEF3C7',
  				dark: '#92400E',
  			},
  			info: {
  				DEFAULT: '#3B82F6',
  				light: '#DBEAFE',
  				dark: '#1E40AF',
  			},
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)',
  			'4xl': '2rem',
  		},
  		fontFamily: {
  			sans: [
  				'var(--font-inter)',
  				'system-ui',
  				'sans-serif'
  			],
  			display: [
  				'var(--font-cal)',
  				'system-ui',
  				'sans-serif'
  			]
  		},
  		screens: {
  			'xs': '375px',
  		},
  		spacing: {
  			'18': '4.5rem',
  			'88': '22rem',
  			'touch': '44px',
  		},
  		keyframes: {
  			'accordion-down': {
  				from: { height: '0' },
  				to: { height: 'var(--radix-accordion-content-height)' }
  			},
  			'accordion-up': {
  				from: { height: 'var(--radix-accordion-content-height)' },
  				to: { height: '0' }
  			},
  			shimmer: {
  				'0%': { backgroundPosition: '-200% 0' },
  				'100%': { backgroundPosition: '200% 0' }
  			},
  			'fade-in': {
  				from: { opacity: '0', transform: 'translateY(8px)' },
  				to: { opacity: '1', transform: 'translateY(0)' }
  			},
  			'fade-in-up': {
  				from: { opacity: '0', transform: 'translateY(16px)' },
  				to: { opacity: '1', transform: 'translateY(0)' }
  			},
  			'slide-up': {
  				from: { transform: 'translateY(10px)', opacity: '0' },
  				to: { transform: 'translateY(0)', opacity: '1' }
  			},
  			'slide-down': {
  				from: { transform: 'translateY(-10px)', opacity: '0' },
  				to: { transform: 'translateY(0)', opacity: '1' }
  			},
  			'slide-in-right': {
  				from: { transform: 'translateX(10px)', opacity: '0' },
  				to: { transform: 'translateX(0)', opacity: '1' }
  			},
  			'slide-in-left': {
  				from: { transform: 'translateX(-10px)', opacity: '0' },
  				to: { transform: 'translateX(0)', opacity: '1' }
  			},
  			'scale-in': {
  				from: { transform: 'scale(0.95)', opacity: '0' },
  				to: { transform: 'scale(1)', opacity: '1' }
  			},
  			'scale-in-bounce': {
  				'0%': { transform: 'scale(0)', opacity: '0' },
  				'50%': { transform: 'scale(1.05)' },
  				'100%': { transform: 'scale(1)', opacity: '1' }
  			},
  			'pulse-soft': {
  				'0%, 100%': { opacity: '1' },
  				'50%': { opacity: '0.7' }
  			},
  			float: {
  				'0%, 100%': { transform: 'translateY(0)' },
  				'50%': { transform: 'translateY(-6px)' }
  			},
  			'gradient-shift': {
  				'0%': { backgroundPosition: '0% 50%' },
  				'50%': { backgroundPosition: '100% 50%' },
  				'100%': { backgroundPosition: '0% 50%' }
  			},
  			'gradient-xy': {
  				'0%, 100%': { backgroundPosition: '0% 0%' },
  				'25%': { backgroundPosition: '100% 0%' },
  				'50%': { backgroundPosition: '100% 100%' },
  				'75%': { backgroundPosition: '0% 100%' },
  			},
  			'border-glow': {
  				'0%, 100%': { borderColor: 'rgba(139, 92, 246, 0.3)' },
  				'50%': { borderColor: 'rgba(139, 92, 246, 0.6)' }
  			},
  			'shine': {
  				from: { backgroundPosition: '200% 0' },
  				to: { backgroundPosition: '-200% 0' }
  			},
  			'spotlight': {
  				'0%': { opacity: '0', transform: 'translate(-50%, -50%) scale(0.5)' },
  				'100%': { opacity: '1', transform: 'translate(-50%, -50%) scale(1)' }
  			},
  			'glow-pulse': {
  				'0%, 100%': { opacity: '1', transform: 'scale(1)' },
  				'50%': { opacity: '0.85', transform: 'scale(1.02)' },
  			},
  			'bounce-soft': {
  				'0%, 100%': { transform: 'translateY(-3%)' },
  				'50%': { transform: 'translateY(0)' },
  			},
  			'wiggle': {
  				'0%, 100%': { transform: 'rotate(-2deg)' },
  				'50%': { transform: 'rotate(2deg)' },
  			},
  			'number-tick': {
  				'0%': { transform: 'translateY(100%)', opacity: '0' },
  				'100%': { transform: 'translateY(0)', opacity: '1' },
  			},
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out',
  			shimmer: 'shimmer 2s infinite linear',
  			'fade-in': 'fade-in 0.4s ease-out',
  			'fade-in-up': 'fade-in-up 0.5s ease-out',
  			'slide-up': 'slide-up 0.4s ease-out',
  			'slide-down': 'slide-down 0.4s ease-out',
  			'slide-in-right': 'slide-in-right 0.3s ease-out',
  			'slide-in-left': 'slide-in-left 0.3s ease-out',
  			'scale-in': 'scale-in 0.3s ease-out',
  			'scale-in-bounce': 'scale-in-bounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  			'pulse-soft': 'pulse-soft 3s ease-in-out infinite',
  			float: 'float 3s ease-in-out infinite',
  			'float-slow': 'float 6s ease-in-out infinite',
  			'gradient-shift': 'gradient-shift 6s ease infinite',
  			'gradient-xy': 'gradient-xy 15s ease infinite',
  			'border-glow': 'border-glow 2s ease-in-out infinite',
  			shine: 'shine 4s linear infinite',
  			spotlight: 'spotlight 0.3s ease-out',
  			'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
  			'glow-pulse-slow': 'glow-pulse 4s ease-in-out infinite',
  			'bounce-soft': 'bounce-soft 1s ease-in-out infinite',
  			'wiggle': 'wiggle 1s ease-in-out infinite',
  			'spin-slow': 'spin 3s linear infinite',
  			'number-tick': 'number-tick 0.4s ease-out',
  		},
  		backgroundImage: {
  			'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
  			'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))',
  			'mesh-gradient': 'radial-gradient(at 40% 20%, hsla(262, 83%, 58%, 0.08) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(289, 100%, 72%, 0.06) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(262, 60%, 50%, 0.05) 0px, transparent 50%)',
  			'mesh-gradient-strong': 'radial-gradient(at 40% 20%, hsla(262, 83%, 58%, 0.15) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(289, 100%, 72%, 0.12) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(262, 60%, 50%, 0.1) 0px, transparent 50%)',
  			'mesh-gradient-warm': 'radial-gradient(at 80% 80%, hsla(142, 71%, 45%, 0.08) 0px, transparent 50%), radial-gradient(at 20% 40%, hsla(340, 82%, 52%, 0.06) 0px, transparent 50%), radial-gradient(at 60% 20%, hsla(262, 83%, 58%, 0.05) 0px, transparent 50%)',
  			'dot-pattern': 'radial-gradient(circle, hsl(220 13% 86%) 1px, transparent 1px)',
  			'shine-gradient': 'linear-gradient(110deg, transparent 25%, rgba(255,255,255,0.5) 50%, transparent 75%)',
  			'gradient-cyber': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  			'gradient-soft': 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
  			'gradient-thermal': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  			'gradient-mermaid': 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
  		},
  		backgroundSize: {
  			'dot-sm': '20px 20px',
  			'dot-md': '30px 30px',
  			'shine': '200% 100%'
  		},
  		backdropBlur: {
  			xs: '2px'
  		},
  		boxShadow: {
  			'glow-sm': '0 0 15px -3px rgba(139, 92, 246, 0.15)',
  			'glow-md': '0 0 25px -5px rgba(139, 92, 246, 0.2)',
  			'glow-lg': '0 0 40px -8px rgba(139, 92, 246, 0.25)',
  			'glow-xl': '0 0 60px -10px rgba(139, 92, 246, 0.3)',
  			'inner-glow': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
  			'card-hover': '0 20px 40px -15px rgba(0, 0, 0, 0.1), 0 0 20px -5px rgba(139, 92, 246, 0.1)',
  			'elevated': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
  			'floating': '0 30px 60px -12px rgba(0, 0, 0, 0.15)',
  		}
  	}
  },
  plugins: [
    require("tailwindcss-animate"),
    require("@tailwindcss/typography"),
    require("tailwindcss-motion"),
  ],
};

export default config;
