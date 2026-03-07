/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // ألوان نوقة الخاصة (Dark Theme)
                noogh: {
                    900: '#0f172a', // خلفية رئيسية
                    800: '#1e293b', // خلفية القوائم
                    500: '#3b82f6', // لون التفاعل (أزرق)
                    accent: '#10b981', // لون النجاح (أخضر)
                }
            }
        },
    },
    plugins: [],
}
