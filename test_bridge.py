import asyncio

async def test_redirect():
    pixel_id = "12345"
    ga_id = "GA-123"
    fb_token = "TOKEN"
    original_url = "https://example.com"
    
    # Copy the logic from web_dashboard.py
    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Carregando oferta...</title>
            <meta http-equiv="refresh" content="{2 if ga_id else 0};url={original_url}">
            
            <!-- Google Analytics -->
            {f'''<script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{ga_id}');
            </script>''' if ga_id else ''}
            
            <!-- Facebook Pixel -->
            {f'''<script>
                !function(f,b,e,v,n,t,s)
                {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
                n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
                if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
                n.queue=[];t=b.createElement(e);t.async=!0;
                t.src=v;s=b.getElementsByTagName(e)[0];
                s.parentNode.insertBefore(t,s)}}(window, document,'script',
                'https://connect.facebook.net/en_US/fbevents.js');
                fbq('init', '{pixel_id}');
                fbq('track', 'PageView');
            </script>''' if pixel_id else ''}
            
            <style>
                body {{ background: #0d1117; color: white; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .loader {{ border: 4px solid #f3f3f3; border-top: 4px solid #58a6ff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            </style>
        </head>
        <body>
            <div style="text-align: center;">
                <div class="loader" style="margin: 0 auto 20px;"></div>
                <p>Você está sendo redirecionado para a oferta...</p>
                <small style="color: #8b949e;">Aguarde um instante.</small>
            </div>
            <script>
                // Backup via JS
                setTimeout(function() {{
                    window.location.href = "{original_url}";
                }}, {2500 if ga_id else 500});
            </script>
        </body>
        </html>
        """
    with open("test_output.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    asyncio.run(test_redirect())
