from typing import Optional
from fastapi import HTTPException
from redis.asyncio import Redis
from src.models.cart import Cart
from src.schemas.cart import CartItem


class CartManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.lock_timeout = 30  # seconds
        self.cart_timeout = 3600  # 1 hour

    async def acquire_lock(self, cart_id: str) -> bool:
        lock_key = f"lock:{cart_id}"
        return await self.redis.set(lock_key, "1", nx=True, ex=self.lock_timeout)

    async def release_lock(self, cart_id: str) -> None:
        lock_key = f"lock:{cart_id}"
        await self.redis.delete(lock_key)

    async def get_cart(self, user_id: str) -> Optional[Cart]:
        cart_key = f"cart:{user_id}"
        cart_data = await self.redis.get(cart_key)
        if not cart_data:
            return None
        return Cart.parse_raw(cart_data)

    async def add_item(self, user_id: str, item: CartItem) -> Cart:
        cart_key = f"cart:{user_id}"

        if not await self.acquire_lock(cart_key):
            raise HTTPException(409, "Cart is locked. Please try again.")

        try:
            cart = await self.get_cart(user_id) or Cart(user_id=user_id, items=[])

            # Check if item already exists
            for existing_item in cart.items:
                if existing_item.lead_id == item.lead_id:
                    existing_item.quantity += item.quantity
                    break
            else:
                cart.items.append(item)

            # Update cart in Redis
            await self.redis.set(cart_key, cart.json(), ex=self.cart_timeout)

            return cart

        finally:
            await self.release_lock(cart_key)

    async def remove_item(self, user_id: str, lead_id: str) -> Cart:
        cart_key = f"cart:{user_id}"

        if not await self.acquire_lock(cart_key):
            raise HTTPException(409, "Cart is locked. Please try again.")

        try:
            cart = await self.get_cart(user_id)
            if not cart:
                raise HTTPException(404, "Cart not found")

            cart.items = [item for item in cart.items if item.lead_id != lead_id]

            await self.redis.set(cart_key, cart.json(), ex=self.cart_timeout)

            return cart

        finally:
            await self.release_lock(cart_key)

    async def clear_cart(self, user_id: str) -> None:
        cart_key = f"cart:{user_id}"
        await self.redis.delete(cart_key)

    async def update_item_quantity(
        self, user_id: str, lead_id: str, quantity: int
    ) -> Cart:
        cart_key = f"cart:{user_id}"

        if not await self.acquire_lock(cart_key):
            raise HTTPException(409, "Cart is locked. Please try again.")

        try:
            cart = await self.get_cart(user_id)
            if not cart:
                raise HTTPException(404, "Cart not found")

            for item in cart.items:
                if item.lead_id == lead_id:
                    item.quantity = quantity
                    break
            else:
                raise HTTPException(404, "Item not found in cart")

            await self.redis.set(cart_key, cart.json(), ex=self.cart_timeout)

            return cart

        finally:
            await self.release_lock(cart_key)
