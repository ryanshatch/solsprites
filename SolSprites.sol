// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SolSprites is ERC721URIStorage, Ownable {
    string private baseTokenURI;
    string private contractMetadataURI;
    uint256 public constant MAX_SUPPLY = 333;
    uint256 public totalMinted = 0;

    constructor(
        string memory _baseTokenURI,
        string memory _contractMetadataURI
    ) ERC721("Sol Sprites", "SPRITE") {
        baseTokenURI = _baseTokenURI;
        contractMetadataURI = _contractMetadataURI;
    }

    function mint(address to, string memory tokenMetadataURI) external onlyOwner {
        require(totalMinted < MAX_SUPPLY, "All sprites minted");
        uint256 tokenId = totalMinted + 1;
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, tokenMetadataURI);
        totalMinted++;
    }

    function contractURI() public view returns (string memory) {
        return contractMetadataURI;
    }

    function setBaseURI(string memory _newBaseURI) external onlyOwner {
        baseTokenURI = _newBaseURI;
    }

    function setContractURI(string memory _newContractURI) external onlyOwner {
        contractMetadataURI = _newContractURI;
    }
}
