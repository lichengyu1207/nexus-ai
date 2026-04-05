"""
经济系统NFT化模块
Economic System NFT Module

实现智能体上链、NFT交易市场、智能体拍卖
"""

import asyncio
import json
import uuid
import time
import hashlib
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class NFTType(Enum):
    AGENT = "agent"
    SKIN = "skin"
    ABILITY = "ability"
    MEMORY = "memory"
    ACHIEVEMENT = "achievement"
    LAND = "land"
    BADGE = "badge"


class NFTStatus(Enum):
    MINTED = "minted"
    LISTED = "listed"
    SOLD = "sold"
    TRANSFERRED = "transferred"
    BURNED = "burned"
    LOCKED = "locked"


class TransactionType(Enum):
    MINT = "mint"
    TRANSFER = "transfer"
    SALE = "sale"
    PURCHASE = "purchase"
    AUCTION_BID = "auction_bid"
    AUCTION_WIN = "auction_win"
    BURN = "burn"
    LOCK = "lock"
    UNLOCK = "unlock"


class AuctionStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


@dataclass
class NFTMetadata:
    name: str
    description: str
    image_url: str
    attributes: Dict[str, Any]
    rarity: str = "common"
    collection: str = ""
    creator: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class AgentNFT:
    nft_id: str
    nft_type: NFTType
    token_id: str
    contract_address: str
    owner_id: str
    metadata: NFTMetadata
    status: NFTStatus = NFTStatus.MINTED
    agent_data: Dict[str, Any] = field(default_factory=dict)
    generation: int = 1
    mutation_count: int = 0
    parent_ids: List[str] = field(default_factory=list)
    energy_level: float = 100.0
    abilities: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    locked_until: float = 0
    royalty_percentage: float = 0.05
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nft_id": self.nft_id,
            "nft_type": self.nft_type.value,
            "token_id": self.token_id,
            "contract_address": self.contract_address,
            "owner_id": self.owner_id,
            "metadata": {
                "name": self.metadata.name,
                "description": self.metadata.description,
                "image_url": self.metadata.image_url,
                "attributes": self.metadata.attributes,
                "rarity": self.metadata.rarity,
                "collection": self.metadata.collection,
                "creator": self.metadata.creator,
            },
            "status": self.status.value,
            "agent_data": self.agent_data,
            "generation": self.generation,
            "mutation_count": self.mutation_count,
            "parent_ids": self.parent_ids,
            "energy_level": self.energy_level,
            "abilities": self.abilities,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "locked_until": self.locked_until,
            "royalty_percentage": self.royalty_percentage,
        }
    
    def compute_hash(self) -> str:
        data = f"{self.nft_id}{self.token_id}{self.owner_id}{json.dumps(self.agent_data, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class NFTTransaction:
    tx_id: str
    tx_type: TransactionType
    nft_id: str
    from_address: str
    to_address: str
    price: float = 0
    currency: str = "FDC"
    gas_fee: float = 0
    timestamp: float = field(default_factory=time.time)
    block_number: int = 0
    tx_hash: str = ""
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type.value,
            "nft_id": self.nft_id,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "price": self.price,
            "currency": self.currency,
            "gas_fee": self.gas_fee,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "tx_hash": self.tx_hash,
            "status": self.status,
            "metadata": self.metadata,
        }


@dataclass
class Auction:
    auction_id: str
    nft_id: str
    seller_id: str
    starting_price: float
    current_price: float
    reserve_price: Optional[float] = None
    duration: int = 86400
    status: AuctionStatus = AuctionStatus.PENDING
    bids: List[Dict[str, Any]] = field(default_factory=list)
    winner_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    ends_at: float = 0
    finalized_at: Optional[float] = None
    
    def __post_init__(self):
        if self.ends_at == 0:
            self.ends_at = self.created_at + self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "auction_id": self.auction_id,
            "nft_id": self.nft_id,
            "seller_id": self.seller_id,
            "starting_price": self.starting_price,
            "current_price": self.current_price,
            "reserve_price": self.reserve_price,
            "duration": self.duration,
            "status": self.status.value,
            "bids": self.bids,
            "winner_id": self.winner_id,
            "created_at": self.created_at,
            "ends_at": self.ends_at,
            "finalized_at": self.finalized_at,
        }
    
    def is_active(self) -> bool:
        return self.status == AuctionStatus.ACTIVE and time.time() < self.ends_at
    
    def place_bid(self, bidder_id: str, amount: float) -> bool:
        if not self.is_active():
            return False
        
        if amount <= self.current_price:
            return False
        
        self.bids.append({
            "bidder_id": bidder_id,
            "amount": amount,
            "timestamp": time.time(),
        })
        self.current_price = amount
        return True


@dataclass
class MarketplaceListing:
    listing_id: str
    nft_id: str
    seller_id: str
    price: float
    currency: str = "FDC"
    quantity: int = 1
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0
    is_active: bool = True
    
    def __post_init__(self):
        if self.expires_at == 0:
            self.expires_at = self.created_at + 86400 * 7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "nft_id": self.nft_id,
            "seller_id": self.seller_id,
            "price": self.price,
            "currency": self.currency,
            "quantity": self.quantity,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
        }


RARITY_WEIGHTS = {
    "common": 1.0,
    "uncommon": 1.5,
    "rare": 2.0,
    "epic": 3.0,
    "legendary": 5.0,
    "mythic": 10.0,
}

ABILITY_TYPES = {
    "valuation_accuracy": "估价精度",
    "risk_detection": "风险检测",
    "market_prediction": "市场预测",
    "customer_insight": "客户洞察",
    "policy_analysis": "政策分析",
    "teaching_ability": "教学能力",
    "compliance_check": "合规检查",
}


class NFTMinter:
    def __init__(self, contract_address: str = "0x1234567890abcdef"):
        self.contract_address = contract_address
        self._token_counter = 0
    
    async def mint_agent_nft(self, owner_id: str, agent_data: Dict[str, Any],
                              metadata: NFTMetadata,
                              parent_ids: List[str] = None) -> AgentNFT:
        self._token_counter += 1
        
        nft_id = str(uuid.uuid4())
        token_id = f"{self.contract_address}:{self._token_counter}"
        
        generation = 1
        mutation_count = 0
        
        if parent_ids:
            generation = max(1, len(parent_ids)) + 1
        
        abilities = self._generate_abilities(agent_data, metadata.rarity)
        
        nft = AgentNFT(
            nft_id=nft_id,
            nft_type=NFTType.AGENT,
            token_id=token_id,
            contract_address=self.contract_address,
            owner_id=owner_id,
            metadata=metadata,
            status=NFTStatus.MINTED,
            agent_data=agent_data,
            generation=generation,
            mutation_count=mutation_count,
            parent_ids=parent_ids or [],
            abilities=abilities,
        )
        
        logger.info(f"NFT minted: {nft_id} for owner {owner_id}")
        return nft
    
    def _generate_abilities(self, agent_data: Dict[str, Any], rarity: str) -> Dict[str, float]:
        base_abilities = {ability: 0.5 for ability in ABILITY_TYPES}
        
        rarity_multiplier = RARITY_WEIGHTS.get(rarity, 1.0)
        
        for ability in base_abilities:
            base_abilities[ability] = min(1.0, base_abilities[ability] * rarity_multiplier * (0.8 + 0.4 * hash(str(uuid.uuid4())) % 100 / 100))
        
        if "specialization" in agent_data:
            spec = agent_data["specialization"]
            if spec in base_abilities:
                base_abilities[spec] = min(1.0, base_abilities[spec] * 1.5)
        
        return base_abilities


class NFTMarketplace:
    def __init__(self, blockchain_client: Optional[Any] = None):
        self.blockchain_client = blockchain_client
        
        self._nfts: Dict[str, AgentNFT] = {}
        self._transactions: Dict[str, NFTTransaction] = {}
        self._auctions: Dict[str, Auction] = {}
        self._listings: Dict[str, MarketplaceListing] = {}
        self._owner_nfts: Dict[str, Set[str]] = defaultdict(set)
        
        self._minter = NFTMinter()
        self._lock = asyncio.Lock()
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        self._platform_fee = 0.025
        self._royalty_fee = 0.05
    
    async def start(self) -> None:
        self._running = True
        self._tasks.append(asyncio.create_task(self._process_auctions()))
        self._tasks.append(asyncio.create_task(self._cleanup_expired_listings()))
        logger.info("NFTMarketplace started")
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("NFTMarketplace stopped")
    
    async def mint_agent(self, owner_id: str, agent_data: Dict[str, Any],
                          name: str, description: str, image_url: str,
                          rarity: str = "common", collection: str = "",
                          parent_ids: List[str] = None) -> AgentNFT:
        async with self._lock:
            metadata = NFTMetadata(
                name=name,
                description=description,
                image_url=image_url,
                attributes=agent_data,
                rarity=rarity,
                collection=collection,
                creator=owner_id,
            )
            
            nft = await self._minter.mint_agent_nft(
                owner_id=owner_id,
                agent_data=agent_data,
                metadata=metadata,
                parent_ids=parent_ids,
            )
            
            self._nfts[nft.nft_id] = nft
            self._owner_nfts[owner_id].add(nft.nft_id)
            
            tx = NFTTransaction(
                tx_id=str(uuid.uuid4()),
                tx_type=TransactionType.MINT,
                nft_id=nft.nft_id,
                from_address="0x0",
                to_address=owner_id,
                status="confirmed",
            )
            self._transactions[tx.tx_id] = tx
            
            return nft
    
    async def transfer_nft(self, nft_id: str, from_owner: str, to_owner: str) -> Optional[NFTTransaction]:
        async with self._lock:
            nft = self._nfts.get(nft_id)
            if not nft:
                return None
            
            if nft.owner_id != from_owner:
                return None
            
            if nft.status == NFTStatus.LOCKED:
                return None
            
            nft.owner_id = to_owner
            nft.status = NFTStatus.TRANSFERRED
            nft.updated_at = time.time()
            
            self._owner_nfts[from_owner].discard(nft_id)
            self._owner_nfts[to_owner].add(nft_id)
            
            tx = NFTTransaction(
                tx_id=str(uuid.uuid4()),
                tx_type=TransactionType.TRANSFER,
                nft_id=nft_id,
                from_address=from_owner,
                to_address=to_owner,
                status="confirmed",
            )
            self._transactions[tx.tx_id] = tx
            
            logger.info(f"NFT {nft_id} transferred from {from_owner} to {to_owner}")
            return tx
    
    async def list_for_sale(self, nft_id: str, seller_id: str, price: float,
                             currency: str = "FDC", duration: int = 604800) -> Optional[MarketplaceListing]:
        async with self._lock:
            nft = self._nfts.get(nft_id)
            if not nft or nft.owner_id != seller_id:
                return None
            
            if nft.status == NFTStatus.LOCKED:
                return None
            
            nft.status = NFTStatus.LISTED
            
            listing = MarketplaceListing(
                listing_id=str(uuid.uuid4()),
                nft_id=nft_id,
                seller_id=seller_id,
                price=price,
                currency=currency,
                expires_at=time.time() + duration,
            )
            
            self._listings[listing.listing_id] = listing
            
            logger.info(f"NFT {nft_id} listed for sale at {price} {currency}")
            return listing
    
    async def purchase_nft(self, listing_id: str, buyer_id: str) -> Optional[NFTTransaction]:
        async with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or not listing.is_active:
                return None
            
            nft = self._nfts.get(listing.nft_id)
            if not nft:
                return None
            
            platform_fee = listing.price * self._platform_fee
            royalty_fee = listing.price * nft.royalty_percentage
            seller_proceeds = listing.price - platform_fee - royalty_fee
            
            nft.owner_id = buyer_id
            nft.status = NFTStatus.SOLD
            nft.updated_at = time.time()
            
            self._owner_nfts[listing.seller_id].discard(nft.nft_id)
            self._owner_nfts[buyer_id].add(nft.nft_id)
            
            listing.is_active = False
            
            tx = NFTTransaction(
                tx_id=str(uuid.uuid4()),
                tx_type=TransactionType.PURCHASE,
                nft_id=nft.nft_id,
                from_address=listing.seller_id,
                to_address=buyer_id,
                price=listing.price,
                currency=listing.currency,
                gas_fee=platform_fee + royalty_fee,
                status="confirmed",
                metadata={
                    "platform_fee": platform_fee,
                    "royalty_fee": royalty_fee,
                    "seller_proceeds": seller_proceeds,
                },
            )
            self._transactions[tx.tx_id] = tx
            
            logger.info(f"NFT {nft.nft_id} purchased by {buyer_id} for {listing.price}")
            return tx
    
    async def create_auction(self, nft_id: str, seller_id: str,
                              starting_price: float, reserve_price: float = None,
                              duration: int = 86400) -> Optional[Auction]:
        async with self._lock:
            nft = self._nfts.get(nft_id)
            if not nft or nft.owner_id != seller_id:
                return None
            
            if nft.status == NFTStatus.LOCKED:
                return None
            
            nft.status = NFTStatus.LISTED
            
            auction = Auction(
                auction_id=str(uuid.uuid4()),
                nft_id=nft_id,
                seller_id=seller_id,
                starting_price=starting_price,
                current_price=starting_price,
                reserve_price=reserve_price,
                duration=duration,
                status=AuctionStatus.ACTIVE,
            )
            
            self._auctions[auction.auction_id] = auction
            
            logger.info(f"Auction created for NFT {nft_id} starting at {starting_price}")
            return auction
    
    async def place_bid(self, auction_id: str, bidder_id: str, amount: float) -> bool:
        async with self._lock:
            auction = self._auctions.get(auction_id)
            if not auction:
                return False
            
            if auction.seller_id == bidder_id:
                return False
            
            return auction.place_bid(bidder_id, amount)
    
    async def _process_auctions(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(10)
                
                async with self._lock:
                    current_time = time.time()
                    
                    for auction in list(self._auctions.values()):
                        if auction.status == AuctionStatus.ACTIVE and current_time >= auction.ends_at:
                            await self._finalize_auction(auction)
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auction processing error: {e}")
    
    async def _finalize_auction(self, auction: Auction) -> None:
        if not auction.bids:
            auction.status = AuctionStatus.CANCELLED
            nft = self._nfts.get(auction.nft_id)
            if nft:
                nft.status = NFTStatus.MINTED
            return
        
        winning_bid = max(auction.bids, key=lambda b: b["amount"])
        auction.winner_id = winning_bid["bidder_id"]
        auction.status = AuctionStatus.ENDED
        auction.finalized_at = time.time()
        
        nft = self._nfts.get(auction.nft_id)
        if nft:
            nft.owner_id = auction.winner_id
            nft.status = NFTStatus.SOLD
            nft.updated_at = time.time()
            
            self._owner_nfts[auction.seller_id].discard(nft.nft_id)
            self._owner_nfts[auction.winner_id].add(nft.nft_id)
            
            platform_fee = auction.current_price * self._platform_fee
            royalty_fee = auction.current_price * nft.royalty_percentage
            
            tx = NFTTransaction(
                tx_id=str(uuid.uuid4()),
                tx_type=TransactionType.AUCTION_WIN,
                nft_id=nft.nft_id,
                from_address=auction.seller_id,
                to_address=auction.winner_id,
                price=auction.current_price,
                gas_fee=platform_fee + royalty_fee,
                status="confirmed",
            )
            self._transactions[tx.tx_id] = tx
        
        logger.info(f"Auction {auction.auction_id} finalized, winner: {auction.winner_id}")
    
    async def _cleanup_expired_listings(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(3600)
                
                async with self._lock:
                    current_time = time.time()
                    
                    for listing in list(self._listings.values()):
                        if listing.is_active and current_time >= listing.expires_at:
                            listing.is_active = False
                            nft = self._nfts.get(listing.nft_id)
                            if nft and nft.status == NFTStatus.LISTED:
                                nft.status = NFTStatus.MINTED
                            logger.info(f"Listing {listing.listing_id} expired")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Listing cleanup error: {e}")
    
    async def breed_agents(self, parent1_id: str, parent2_id: str, owner_id: str) -> Optional[AgentNFT]:
        async with self._lock:
            parent1 = self._nfts.get(parent1_id)
            parent2 = self._nfts.get(parent2_id)
            
            if not parent1 or not parent2:
                return None
            
            if parent1.owner_id != owner_id or parent2.owner_id != owner_id:
                return None
            
            child_abilities = {}
            for ability in ABILITY_TYPES:
                child_abilities[ability] = (parent1.abilities.get(ability, 0.5) + 
                                            parent2.abilities.get(ability, 0.5)) / 2
                mutation = (hash(str(uuid.uuid4())) % 100) / 100 * 0.2 - 0.1
                child_abilities[ability] = max(0, min(1, child_abilities[ability] + mutation))
            
            child_data = {
                "parent1_id": parent1_id,
                "parent2_id": parent2_id,
                "breeding_timestamp": time.time(),
            }
            
            child_rarity = self._calculate_child_rarity(parent1.metadata.rarity, parent2.metadata.rarity)
            
            metadata = NFTMetadata(
                name=f"{parent1.metadata.name} x {parent2.metadata.name} Offspring",
                description=f"Bred from {parent1.metadata.name} and {parent2.metadata.name}",
                image_url="",
                attributes=child_data,
                rarity=child_rarity,
                creator=owner_id,
            )
            
            child_nft = await self._minter.mint_agent_nft(
                owner_id=owner_id,
                agent_data=child_data,
                metadata=metadata,
                parent_ids=[parent1_id, parent2_id],
            )
            
            child_nft.abilities = child_abilities
            child_nft.generation = max(parent1.generation, parent2.generation) + 1
            
            self._nfts[child_nft.nft_id] = child_nft
            self._owner_nfts[owner_id].add(child_nft.nft_id)
            
            logger.info(f"New agent bred: {child_nft.nft_id} from {parent1_id} x {parent2_id}")
            return child_nft
    
    def _calculate_child_rarity(self, rarity1: str, rarity2: str) -> str:
        rarity_order = ["common", "uncommon", "rare", "epic", "legendary", "mythic"]
        
        idx1 = rarity_order.index(rarity1) if rarity1 in rarity_order else 0
        idx2 = rarity_order.index(rarity2) if rarity2 in rarity_order else 0
        
        base_idx = max(idx1, idx2)
        
        upgrade_chance = (base_idx + 1) * 0.1
        if hash(str(uuid.uuid4())) % 100 / 100 < upgrade_chance and base_idx < len(rarity_order) - 1:
            base_idx += 1
        
        return rarity_order[base_idx]
    
    async def get_nft(self, nft_id: str) -> Optional[AgentNFT]:
        return self._nfts.get(nft_id)
    
    async def get_nfts_by_owner(self, owner_id: str) -> List[AgentNFT]:
        nft_ids = self._owner_nfts.get(owner_id, set())
        return [self._nfts[nid] for nid in nft_ids if nid in self._nfts]
    
    async def get_active_listings(self, limit: int = 50) -> List[MarketplaceListing]:
        return [l for l in self._listings.values() if l.is_active][:limit]
    
    async def get_active_auctions(self, limit: int = 50) -> List[Auction]:
        return [a for a in self._auctions.values() if a.status == AuctionStatus.ACTIVE][:limit]
    
    async def get_transaction_history(self, nft_id: str = None, limit: int = 100) -> List[NFTTransaction]:
        txs = list(self._transactions.values())
        if nft_id:
            txs = [t for t in txs if t.nft_id == nft_id]
        return sorted(txs, key=lambda t: t.timestamp, reverse=True)[:limit]
    
    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_nfts": len(self._nfts),
            "total_transactions": len(self._transactions),
            "active_listings": len([l for l in self._listings.values() if l.is_active]),
            "active_auctions": len([a for a in self._auctions.values() if a.status == AuctionStatus.ACTIVE]),
            "total_owners": len(self._owner_nfts),
            "by_rarity": self._count_by_rarity(),
            "by_status": self._count_by_status(),
        }
    
    def _count_by_rarity(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for nft in self._nfts.values():
            counts[nft.metadata.rarity] += 1
        return dict(counts)
    
    def _count_by_status(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for nft in self._nfts.values():
            counts[nft.status.value] += 1
        return dict(counts)


class NFTMarketplaceMonitor:
    def __init__(self, marketplace: NFTMarketplace):
        self.marketplace = marketplace
        self._metrics_history: List[Dict[str, Any]] = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        stats = await self.marketplace.get_statistics()
        
        metrics = {
            "timestamp": time.time(),
            **stats,
        }
        
        self._metrics_history.append(metrics)
        return metrics
    
    async def get_floor_prices(self) -> Dict[str, float]:
        listings = await self.marketplace.get_active_listings()
        
        by_rarity = defaultdict(list)
        for listing in listings:
            nft = self.marketplace._nfts.get(listing.nft_id)
            if nft:
                by_rarity[nft.metadata.rarity].append(listing.price)
        
        return {
            rarity: min(prices) if prices else 0
            for rarity, prices in by_rarity.items()
        }
    
    async def get_volume_stats(self, hours: int = 24) -> Dict[str, float]:
        cutoff = time.time() - hours * 3600
        
        recent_txs = [
            t for t in self.marketplace._transactions.values()
            if t.timestamp >= cutoff and t.tx_type in [TransactionType.PURCHASE, TransactionType.AUCTION_WIN]
        ]
        
        total_volume = sum(t.price for t in recent_txs)
        tx_count = len(recent_txs)
        
        return {
            "period_hours": hours,
            "total_volume": total_volume,
            "transaction_count": tx_count,
            "average_price": total_volume / tx_count if tx_count > 0 else 0,
        }
    
    async def get_breeding_stats(self) -> Dict[str, Any]:
        bred_nfts = [n for n in self.marketplace._nfts.values() if n.parent_ids]
        
        generations = defaultdict(int)
        for nft in bred_nfts:
            generations[nft.generation] += 1
        
        return {
            "total_bred": len(bred_nfts),
            "by_generation": dict(generations),
            "max_generation": max(generations.keys()) if generations else 0,
        }
