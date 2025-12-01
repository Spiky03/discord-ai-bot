import disnake
from disnake.ext import commands
import base64
import io
from ..utils import make_stable_diffusion_request, log_error

class Text2Img(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="text2img", description="Convert text to image")
    async def text2img(
        self,
        inter: disnake.ApplicationCommandInteraction,
        prompt: str,
        width: int = commands.Param(default=256, min_value=128, max_value=1024),
        height: int = commands.Param(default=256, min_value=128, max_value=1024),
        steps: int = commands.Param(default=10, min_value=5, max_value=20),
        batch_count: int = commands.Param(default=1, min_value=1, max_value=4),
        batch_size: int = commands.Param(default=1, min_value=1, max_value=5),
        enhance_prompt: bool = False
    ):
        await inter.response.defer()
        
        try:
            payload = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps,
                "num_inference_steps": steps,
                "batch_count": batch_count,
                "batch_size": batch_size,
                "enhance_prompt": "yes" if enhance_prompt else "no"
            }
            
            response = await make_stable_diffusion_request("/sdapi/v1/txt2img", "post", payload)
            
            images = []
            for img_str in response.get("images", []):
                img_bytes = base64.b64decode(img_str)
                images.append(disnake.File(io.BytesIO(img_bytes), filename="image.png"))
                
            await inter.edit_original_response(
                content=f"Here are images from prompt `{prompt}`",
                files=images
            )
            
        except Exception as e:
            log_error(e)
            await inter.edit_original_response(content="Error, please check the console")

def setup(bot):
    bot.add_cog(Text2Img(bot))
