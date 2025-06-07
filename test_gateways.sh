#!/bin/bash
# IPFS Gateway Risk Tester - Quick Test Scripts
# =============================================

echo ""
echo "🌐 IPFS Gateway Risk Tester"
echo "==========================="

show_menu() {
    echo ""
    echo "Choose a test option:"
    echo "1. Test 3 random well-known CIDs (quick test)"
    echo "2. Test 10 random well-known CIDs (comprehensive)"
    echo "3. Test custom CIDs (enter manually)"
    echo "4. Test CIDs from file"
    echo "5. Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            echo ""
            echo "🚀 Testing 3 random CIDs with 5 gateways..."
            python3 gateway_risk_tester.py --random-test 3 --gateways 5
            ;;
        2)
            echo ""
            echo "🚀 Testing 10 random CIDs with 8 gateways..."
            python3 gateway_risk_tester.py --random-test 10 --gateways 8
            ;;
        3)
            echo ""
            read -p "Enter CIDs (comma-separated): " custom_cids
            echo "🚀 Testing custom CIDs..."
            python3 gateway_risk_tester.py --cids "$custom_cids" --gateways 6
            ;;
        4)
            echo ""
            read -p "Enter filename containing CIDs: " filename
            echo "🚀 Testing CIDs from file..."
            python3 gateway_risk_tester.py --file "$filename" --gateways 6
            ;;
        5)
            echo ""
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
done 