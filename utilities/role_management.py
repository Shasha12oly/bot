"""
Role Management Commands
Commands to manage roles after initial setup
"""
import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID
from utilities.embed_utils import create_embed


async def add_role_command(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    """Add a role to a member"""
    # Check if user has permission
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff and not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)
        return

    try:
        await member.add_roles(role)
        embed = create_embed(
            title="✅ Role Added",
            description=f"Added role {role.mention} to {member.mention}",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error adding role: {str(e)}", ephemeral=True)


async def remove_role_command(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    """Remove a role from a member"""
    # Check if user has permission
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff and not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)
        return

    try:
        await member.remove_roles(role)
        embed = create_embed(
            title="✅ Role Removed",
            description=f"Removed role {role.mention} from {member.mention}",
            color=discord.Color.orange(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error removing role: {str(e)}", ephemeral=True)


async def list_roles_command(interaction: discord.Interaction):
    """List all roles in the server"""
    roles = interaction.guild.roles[1:]  # Skip @everyone

    embed = create_embed(
        title="📋 Server Roles",
        description=f"Total roles: {len(roles)}",
        color=discord.Color.from_rgb(114, 137, 218),
        message_type="general"
    )

    # Group roles by type (hoisted vs non-hoisted)
    hoisted = [r for r in roles if r.hoist]
    non_hoisted = [r for r in roles if not r.hoist]

    if hoisted:
        hoisted_list = "\n".join([f"• {r.mention} ({r.members} members)" for r in hoisted[:10]])
        if len(hoisted) > 10:
            hoisted_list += f"\n... and {len(hoisted) - 10} more"
        embed.add_field(name="🔝 Displayed Separately", value=hoisted_list or "None", inline=False)

    if non_hoisted:
        non_hoisted_list = "\n".join([f"• {r.mention} ({r.members} members)" for r in non_hoisted[:10]])
        if len(non_hoisted) > 10:
            non_hoisted_list += f"\n... and {len(non_hoisted) - 10} more"
        embed.add_field(name="📁 Other Roles", value=non_hoisted_list or "None", inline=False)

    await interaction.response.send_message(embed=embed)


async def role_info_command(interaction: discord.Interaction, role: discord.Role):
    """Show detailed information about a role"""
    embed = create_embed(
        title=f"📋 Role Info: {role.name}",
        description=f"ID: {role.id}",
        color=role.color,
        message_type="general",
        fields=[
            ("👥 Members", str(len(role.members)), True),
            ("🔝 Hoisted", "Yes" if role.hoist else "No", True),
            ("📢 Mentionable", "Yes" if role.mentionable else "No", True),
            ("🎨 Color", str(role.color), True),
            ("📅 Created", role.created_at.strftime("%Y-%m-%d"), True),
            ("🔗 Position", str(role.position), True)
        ]
    )

    # Show key permissions
    key_perms = []
    if role.permissions.administrator:
        key_perms.append("👑 Administrator")
    if role.permissions.manage_guild:
        key_perms.append("🏢 Manage Server")
    if role.permissions.manage_roles:
        key_perms.append("👥 Manage Roles")
    if role.permissions.manage_channels:
        key_perms.append("📁 Manage Channels")
    if role.permissions.moderate_members:
        key_perms.append("🔨 Moderate Members")
    if role.permissions.kick_members:
        key_perms.append("👢 Kick Members")
    if role.permissions.ban_members:
        key_perms.append("🔨 Ban Members")

    if key_perms:
        embed.add_field(name="🔑 Key Permissions", value=", ".join(key_perms), inline=False)

    await interaction.response.send_message(embed=embed)


async def mute_command(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    """Mute a member by adding the Muted role"""
    # Check if user has permission
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff and not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You don't have permission to mute members.", ephemeral=True)
        return

    # Find the Muted role
    muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not muted_role:
        await interaction.response.send_message("Muted role not found. Please run the role setup script first.", ephemeral=True)
        return

    try:
        await member.add_roles(muted_role, reason=reason or f"Muted by {interaction.user}")
        embed = create_embed(
            title="🔇 Member Muted",
            description=f"{member.mention} has been muted",
            color=discord.Color.red(),
            message_type="general"
        )
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error muting member: {str(e)}", ephemeral=True)


async def unmute_command(interaction: discord.Interaction, member: discord.Member):
    """Unmute a member by removing the Muted role"""
    # Check if user has permission
    is_staff = any(r.id == SUPPORT_ROLE_ID for r in interaction.user.roles)
    if not is_staff and not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("You don't have permission to unmute members.", ephemeral=True)
        return

    # Find the Muted role
    muted_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not muted_role:
        await interaction.response.send_message("Muted role not found.", ephemeral=True)
        return

    try:
        await member.remove_roles(muted_role, reason=f"Unmuted by {interaction.user}")
        embed = create_embed(
            title="🔊 Member Unmuted",
            description=f"{member.mention} has been unmuted",
            color=discord.Color.green(),
            message_type="general"
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error unmuting member: {str(e)}", ephemeral=True)
