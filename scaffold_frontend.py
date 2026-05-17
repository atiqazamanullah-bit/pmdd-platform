import os

dirs = [
    "frontend/src/app/upload",
    "frontend/src/app/dashboard",
    "frontend/src/components/ui",
    "frontend/src/components/dashboard",
    "frontend/src/lib",
    "frontend/public"
]

files = {
    "frontend/package.json": """{
  "name": "pmdd-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.3",
    "react": "^18",
    "react-dom": "^18",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.358.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "postcss": "^8",
    "eslint": "^8",
    "eslint-config-next": "14.1.3"
  }
}
""",

    "frontend/tsconfig.json": """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
""",

    "frontend/tailwind.config.ts": """import type { Config } from "tailwindcss";
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
export default config;
""",

    "frontend/src/app/layout.tsx": """import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PMDD Dashboard",
  description: "Agentic Linguistic Analyzer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
""",

    "frontend/src/app/page.tsx": """import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">Pragmatic Meaning Drift Detector</h1>
      <p className="text-lg text-gray-600 mb-8">Agentic Computational Linguistics Platform</p>
      <div className="flex gap-4">
        <Link href="/upload" className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Upload Corpus</Link>
        <Link href="/dashboard" className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-100">View Dashboard</Link>
      </div>
    </main>
  );
}
""",

    "frontend/src/app/upload/page.tsx": """export default function UploadPage() {
  return (
    <div className="p-10">
      <h2 className="text-2xl font-bold mb-4">Upload Corpus</h2>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
        <p className="text-gray-500">Drag and drop corpus files (.txt, .csv) here or click to browse.</p>
        <input type="file" className="hidden" id="file-upload" />
        <label htmlFor="file-upload" className="mt-4 inline-block px-4 py-2 bg-gray-200 cursor-pointer rounded">Select Files</label>
      </div>
    </div>
  );
}
""",

    "frontend/src/app/dashboard/page.tsx": """export default function Dashboard() {
  return (
    <div className="p-10 flex gap-6">
      <aside className="w-64 bg-white shadow p-4 rounded-lg">
        <nav className="space-y-2">
          <a href="#" className="block p-2 bg-blue-50 text-blue-700 rounded">Overview</a>
          <a href="#" className="block p-2 text-gray-600 hover:bg-gray-50 rounded">Reports</a>
          <a href="#" className="block p-2 text-gray-600 hover:bg-gray-50 rounded">Settings</a>
        </nav>
      </aside>
      <main className="flex-1">
        <h2 className="text-2xl font-bold mb-4">Research Overview</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white shadow p-6 rounded-lg">Total Corpora: 12</div>
          <div className="bg-white shadow p-6 rounded-lg">Active Agents: 5</div>
          <div className="bg-white shadow p-6 rounded-lg">Completed Analyses: 45</div>
        </div>
      </main>
    </div>
  );
}
""",

    "frontend/src/app/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;
"""
}

def scaffold_frontend():
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
    print("Frontend Scaffolding complete.")

if __name__ == "__main__":
    scaffold_frontend()
